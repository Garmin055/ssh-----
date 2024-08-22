#!/bin/bash

# 경로 설정
MAIN_PY_SOURCE="main.py"  # main.py 파일 경로
MAIN_PY_TARGET="/usr/local/bin/ssh_monitor.py"  # 시스템에 복사될 경로
WEBHOOK_PATH="/usr/local/bin/webhook.txt"
SERVICE_PATH="/etc/systemd/system/ssh_monitor.service"

# 1. Python 스크립트 복사
echo "Copying main.py to /usr/local/bin/ssh_monitor.py..."
if [ -f "$MAIN_PY_SOURCE" ]; then
    sudo cp "$MAIN_PY_SOURCE" "$MAIN_PY_TARGET"
    sudo chmod +x "$MAIN_PY_TARGET"
    echo "Python script copied successfully."
else
    echo "Error: main.py file not found in the current directory."
    exit 1
fi

# 2. 세션별 히스토리 설정
echo "Setting up session-based history in ~/.bashrc..."
if ! grep -q "HISTFILE=" ~/.bashrc; then
    echo 'export HISTFILE=~/.bash_history_ssh_$(date +%s)_$$' >> ~/.bashrc
    echo "Session-based history setup completed."
else
    echo "Session-based history is already configured in ~/.bashrc."
fi

# 3. 로그아웃 시 Python 스크립트 실행 설정
echo "Setting up logout script in ~/.bash_logout..."
if [ ! -f ~/.bash_logout ]; then
    touch ~/.bash_logout
fi

if ! grep -q "$MAIN_PY_TARGET" ~/.bash_logout; then
    echo "SSH_ACTION=logout python3 $MAIN_PY_TARGET" >> ~/.bash_logout
    echo "Logout script setup completed."
else
    echo "Logout script is already configured in ~/.bash_logout."
fi

# 4. 웹훅 URL 설정
echo "Setting up webhook URL..."
if [ ! -f "$WEBHOOK_PATH" ]; then
    read -p "Enter your webhook URL: " WEBHOOK_URL
    echo "$WEBHOOK_URL" | sudo tee "$WEBHOOK_PATH" > /dev/null
    echo "Webhook URL saved successfully."
else
    echo "Webhook URL is already set at $WEBHOOK_PATH."
fi

# 5. systemd 서비스 파일 생성
echo "Creating systemd service for the SSH monitor..."
sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=SSH Monitor Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 $MAIN_PY_TARGET
WorkingDirectory=/usr/local/bin/
Restart=always
User=root
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# 6. 서비스 활성화 및 시작
echo "Enabling and starting the SSH monitor service..."
sudo systemctl daemon-reload
sudo systemctl enable ssh_monitor.service
sudo systemctl start ssh_monitor.service

echo "Service ssh_monitor.service has been enabled and started."

# 7. 완료 메시지
echo "Installation completed successfully!"
