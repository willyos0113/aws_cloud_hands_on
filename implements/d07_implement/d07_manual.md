# CLI 部分

1. aws s3 cp hello.txt s3://你的桶/ --profile admin
2. aws s3api list-object-versions --bucket 你的桶 --profile admin
3. aws s3 presign s3://你的桶/hello.txt --expires-in 60 --profile admin

# 路徑

pwd: /Users/yiwei/Desktop/workspace/2026aws/aws_ai/implements/d07_implement

# CLI 指令套入

1. aws s3 cp hello.txt s3://YOUR_BUCKET_NAME/ --profile admin
2. aws s3api list-object-versions --bucket YOUR_BUCKET_NAME --profile admin
3. aws s3 presign s3://YOUR_BUCKET_NAME/hello.txt --expires-in 60 --profile admin
