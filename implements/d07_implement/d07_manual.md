# CLI 部分

1. aws s3 cp hello.txt s3://你的桶/ --profile admin
2. aws s3api list-object-versions --bucket 你的桶 --profile admin
3. aws s3 presign s3://你的桶/hello.txt --expires-in 60 --profile admin

# 路徑

pwd: /Users/yiwei/Desktop/workspace/2026aws/aws_ai/implements/d07_implement

# CLI 指令套入

1. aws s3 cp hello.txt s3://lab-s3-yiweeee01/ --profile admin
2. aws s3api list-object-versions --bucket lab-s3-yiweeee01 --profile admin
3. aws s3 presign s3://lab-s3-yiweeee01/hello.txt --expires-in 60 --profile admin
