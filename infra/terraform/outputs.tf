output "public_ip" { value = aws_instance.k3s.public_ip }
output "ssh_command" { value = "ssh -i ~/.ssh/urlshort ubuntu@${aws_instance.k3s.public_ip}" }
