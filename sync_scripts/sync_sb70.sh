

for target_port in 2201 2202 2203; do
  rsync -avz -e "ssh -i ~/.ssh/id_ed25519 -p $target_port" ./../ root@192.168.2.10:/home/root/zero_export --exclude .venv --exclude .git --exclude .idea --exclude sync_scripts --exclude settings.py
  ssh root@192.168.2.10 -i ~/.ssh/id_ed25519 -p $target_port "reboot"
done

