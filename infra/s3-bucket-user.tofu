provider "aws" {
  region = "us-east-1"
}

# Create the S3 bucket
resource "aws_s3_bucket" "incident_logs" {
  bucket = ""// always unique needs to prioritise secruity

  tags = {
    Name = "Incident Logs Bucket"
  }
}

# Create IAM user
resource "aws_iam_user" "upload_user" {
  name = "logs-uploader"
}

# Create access key for the user
resource "aws_iam_access_key" "upload_key" {
  user = aws_iam_user.upload_user.name
}

# IAM policy allowing put-object to the specific bucket
data "aws_iam_policy_document" "upload_policy" {
  statement {
    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.incident_logs.arn}/*"
    ]

    effect = "Allow"
  }
}

# Attach the policy to the user
resource "aws_iam_user_policy" "upload_policy" {
  name   = "S3UploadPolicy"
  user   = aws_iam_user.upload_user.name
  policy = data.aws_iam_policy_document.upload_policy.json
}

# Outputs
output "bucket_name" {
  value = aws_s3_bucket.incident_logs.bucket
}
