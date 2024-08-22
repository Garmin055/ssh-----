import os
import subprocess
import re
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

try:
    with open('webhook.txt', 'r') as file:
        webhook_url = file.read().strip()
except FileNotFoundError:
    print("webhook.txt 파일을 찾을 수 없습니다.")

# 웹훅 전송 함수 (Discord)
def webhook_send(sendContent):
    
    # Discord 웹훅 요청 생성
    webhook = DiscordWebhook(url=webhook_url, content=sendContent)
    
    try:
        # 웹훅 실행 및 응답 받기
        response = webhook.execute()
        
        # 상태 코드가 200번대면 성공
        if response.status_code // 100 == 2:
            print("웹훅 전송 성공")
        else:
            print(f"웹훅 전송 실패: {response.status_code}, 응답 내용: {response.text}")
    
    except Exception as e:
        print(f"웹훅 전송 중 오류 발생: {e}")

# IP 정보 조회 함수 (ipinfo.io 사용)
def get_ip_info(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        if response.status_code == 200:
            data = response.json()
            country = data.get('country', '알 수 없음')
            org = data.get('org', '')

            # VPN 여부 확인
            is_vpn = "VPN 사용" if "vpn" in org.lower() or "hosting" in org.lower() else "VPN 미사용"

            return {
                "ip_address": ip_address,
                "country": country,
                "is_vpn": is_vpn
            }
        else:
            print(f"IP 정보 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"IP 정보 조회 중 오류 발생: {e}")
        return None

# 세션별 명령어 기록 가져오기
def get_command_history():
    histfile = os.getenv('HISTFILE')  # 세션별로 기록된 히스토리 파일 경로
    if histfile and os.path.exists(histfile):
        try:
            with open(histfile, 'r') as file:
                commands = file.readlines()  # 모든 명령어 가져오기
            return commands
        except Exception as e:
            print(f"명령어 기록을 가져오는 중 오류 발생: {e}")
            return []
    else:
        print("HISTFILE을 찾을 수 없습니다.")
        return []

# SSH 로그인 감지 및 처리
def monitor_ssh_logins():
    process = subprocess.Popen(['journalctl', '-u', 'ssh', '-f'], stdout=subprocess.PIPE)
    
    while True:
        output = process.stdout.readline()
        if output:
            line = output.decode('utf-8').strip()
            match = re.search(r'Accepted \S+ for (\S+) from (\S+)', line)
            
            if match:
                username = match.group(1)
                ip_address = match.group(2)
                print(f"SSH 로그인 감지: {username} from {ip_address}")
                
                # IP 정보 조회
                ip_info = get_ip_info(ip_address)
                if ip_info:
                    sendContent = f"SSH 로그인 감지: {username} from {ip_info['ip_address']} (국가: {ip_info['country']}, VPN 여부: {ip_info['is_vpn']})"
                    webhook_send(sendContent)

# 로그아웃 시 실행
def on_logout():
    username = os.getlogin()
    commands = get_command_history()
    
    if commands:
        sendContent = f"사용자 {username}의 명령어 로그아웃 기록:\n" + "".join(commands)
    else:
        sendContent = f"사용자 {username}의 명령어 기록을 찾을 수 없습니다."
    
    webhook_send(sendContent)

if __name__ == "__main__":
    # 로그아웃 시 실행
    if 'logout' in os.getenv('SSH_ACTION', ''):
        on_logout()
    else:
        monitor_ssh_logins()