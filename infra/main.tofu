provider "aws" {
  region = "us-east-1"
}

# Get the existing key pair
data "aws_key_pair" "k8s_key" {
  key_name = ""//it confidentiallll
}

# Get the existing security group by name
data "aws_security_group" "launch_wizard_11" {
  filter {
    name   = "group-name"
    values = [""] // this also 
  }
}

# Launch a new EC2 instance
resource "aws_instance" "my_instance" {
  ami           = "ami-084568db4383264d4" 
  instance_type = "t2.micro"
  key_name      = data.aws_key_pair.k8s_key.key_name

  vpc_security_group_ids = [data.aws_security_group.launch_wizard_11.id]

  root_block_device {
    volume_size = 16
    volume_type = "gp2"
  }

  tags = {
    Name = "ok-devops"
  }
}

# Wait until instance is running
resource "null_resource" "wait_for_running" {
  depends_on = [aws_instance.my_instance]

  provisioner "local-exec" {
    command = "aws ec2 wait instance-running --instance-ids ${aws_instance.my_instance.id}"
  }

  triggers = {
    instance_id = aws_instance.my_instance.id
  }
}

# Refetch the instance details after it's running
data "aws_instance" "running_instance" {
  instance_id = aws_instance.my_instance.id
  depends_on  = [null_resource.wait_for_running]
}

# Output public IP
output "instance_public_ip" {
  value       = data.aws_instance.running_instance.public_ip
  description = "Public IP of the EC2 instance after it has started"
}
