output "public_ip" { value = aws_eip.k3s.public_ip }
output "ssh_command" { value = "ssh -i ~/.ssh/urlshort ubuntu@${aws_eip.k3s.public_ip}" }
