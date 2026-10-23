#!/bin/bash

# 請將 ALB_URL 替換為你的 ALB DNS Name
ALB_URL="ha-alb-1619180578.ap-northeast-1.elb.amazonaws.com/health"

while true;
do 
    echo "$(date +%T) $(curl -s -m 2 http://${ALB_URL} || echo 失敗)";
    sleep 1; 
done