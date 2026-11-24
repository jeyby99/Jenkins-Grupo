#!/bin/bash
# User data de la EC2 (Amazon Linux 2023): prepara Docker y la carpeta de trabajo.
set -euo pipefail

dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user
mkdir -p /home/ec2-user/calculadora
chown ec2-user:ec2-user /home/ec2-user/calculadora
