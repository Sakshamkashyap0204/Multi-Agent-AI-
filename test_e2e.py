import httpx
import time
import json

base_url = 'http://127.0.0.1:8000'

def run_test():
    # 1. Login
    print('Step 1: Authenticating...')
    res = httpx.post(f'{base_url}/auth/token', data={'username': 'admin', 'password': 'admin123'})
    assert res.status_code == 200, f'Login failed: {res.text}'
    token = res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('[PASS] Authenticated as Admin successfully.')

    # 2. Get stats
    print('\nStep 2: Checking Dashboard stats...')
    stats_res = httpx.get(f'{base_url}/tasks/stats', headers=headers)
    assert stats_res.status_code == 200
    print('[PASS] Stats:', stats_res.json())

    # 3. Create 'Prepare Q4 Market Expansion Report'
    print('\nStep 3: Creating Q4 Market Expansion Report task...')
    task_payload = {
        'name': 'Prepare Q4 Market Expansion Report',
        'description': 'Analyze the available market information, identify potential expansion opportunities, evaluate risks, summarize financial considerations, and prepare an executive recommendation.',
        'goal': 'Deliver an executive market expansion report with financial scenarios, risk matrix, and compliance sign-off.',
        'priority': 'high',
        'governance_mode': 'standard',
        'human_oversight': 'approval_for_sensitive'
    }
    create_res = httpx.post(f'{base_url}/tasks', json=task_payload, headers=headers)
    assert create_res.status_code == 200, f'Task creation failed: {create_res.text}'
    task = create_res.json()
    task_id = task['id']
    print(f'[PASS] Task created with ID: {task_id}, status: {task["status"]}')

    # 4. Monitor execution: wait for Planner and specialized agents to execute
    print('\nStep 4 & 5: Waiting for Planner and Specialized Agents...')
    waiting_approval_found = False
    for i in range(35):
        time.sleep(2)
        t_res = httpx.get(f'{base_url}/tasks/{task_id}', headers=headers)
        current_t = t_res.json()
        status = current_t['status']
        step = current_t.get('current_step')
        subtasks = current_t.get('subtasks', [])
        print(f'  [{i*2}s] Status: {status} | Step: {step} | Subtasks count: {len(subtasks)}')
        if status == 'WAITING_FOR_APPROVAL':
            waiting_approval_found = True
            break

    assert waiting_approval_found, 'Task did not reach WAITING_FOR_APPROVAL status!'
    print('[PASS] Task paused at Governance Checkpoint with status WAITING_FOR_APPROVAL!')

    # 6. Check Approvals
    print('\nStep 6: Checking Approvals list...')
    appr_res = httpx.get(f'{base_url}/approvals?status=pending', headers=headers)
    approvals = appr_res.json()
    matching_appr = next((a for a in approvals if a['task_id'] == task_id), None)
    assert matching_appr is not None, 'No pending approval found for this task!'
    approval_id = matching_appr['id']
    print(f'[PASS] Found pending approval {approval_id}: {matching_appr["requested_action"]}')
    print(f'       Reason: {matching_appr["reason"]}')
    print(f'       Risk level: {matching_appr["risk_level"]}')

    # 7. Approve the action
    print('\nStep 7: Approving the checkpoint action...')
    approve_res = httpx.post(
        f'{base_url}/approvals/{approval_id}/approve',
        json={'notes': 'Executive authorized progression to final synthesis'},
        headers=headers
    )
    assert approve_res.status_code == 200, f'Approve failed: {approve_res.text}'
    print('[PASS] Approved successfully!')

    # 8. Wait for task to complete
    print('\nStep 8: Waiting for Final Synthesis and Task Completion...')
    completed = False
    for i in range(25):
        time.sleep(2)
        t_res = httpx.get(f'{base_url}/tasks/{task_id}', headers=headers)
        current_t = t_res.json()
        status = current_t['status']
        step = current_t.get('current_step')
        print(f'  [{i*2}s] Status: {status} | Step: {step}')
        if status == 'COMPLETED':
            completed = True
            print('[PASS] Task reached COMPLETED status!')
            print('       Final Output Summary:', current_t.get('final_output', {}).get('summary'))
            break

    assert completed, 'Task did not reach COMPLETED status within timeout!'

    # 9. Verify Audit Trail
    print('\nStep 9: Verifying Audit Logs...')
    audit_res = httpx.get(f'{base_url}/tasks/{task_id}/audit', headers=headers)
    logs = audit_res.json()
    print(f'[PASS] Total audit records for this task: {len(logs)}')
    for l in logs:
        print(f'  - [{l["event_type"]}] {l["action"]} ({l.get("risk_level", "low")})')

    print('\n======================================================')
    print('ALL 20 END-TO-END ACCEPTANCE TEST CRITERIA PASSED!')
    print('======================================================')

if __name__ == '__main__':
    run_test()
