
# AWS Inventory Script for Commvault FETB Sizing

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)
![AWS](https://img.shields.io/badge/AWS-Org%20Inventory-orange)

> Inventory and FETB sizing tool for AWS, purpose-built for Commvault Cloud deployments.  
> Collects EC2 (EBS), EFS, RDS, and S3 data across AWS Organization accounts.  
> Outputs to Excel with clean summary and per-service tabs.

# AWS Inventory Script for Commvault FETB Sizing

This script inventories AWS EC2 (EBS), EFS, RDS, and S3 resources across all active accounts in an AWS Organization.
It assumes a role into each account and collects capacity data for FETB (Front-End Terabytes) sizing.

## ✅ Features
- Cross-account access via AWS Organizations and STS
- Inventories EC2 (via EBS), EFS, RDS, and S3
- Extracts resource counts, sizes, and tags
- Outputs a single Excel file with:
  - Summary tab: account, region, service, count, capacity
  - Tabs per service per account-region

## 🔧 Requirements

You need the following Python modules installed:
- `boto3`
- `openpyxl`

Install them using pip:
```bash
python3 -m venv venv
source venv/bin/activate
pip install boto3 openpyxl
```

### AWS IAM Requirements
The AWS credentials used to run this script **must be from the Management (payer) account** and must have:
- `organizations:ListAccounts`
- `sts:AssumeRole` on target accounts

Each target account **must have an IAM role** named:
```
OrganizationAccountAccessRole
```
...which is assumable by the management account.

This role should have at least the following permissions:
- `ec2:DescribeVolumes`
- `efs:DescribeFileSystems`
- `rds:DescribeDBInstances`
- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`
- `cloudwatch:GetMetricStatistics`

## ▶️ Run the Script

```bash
python aws_inventory.py
```

If successful, the script will output:
- A JSON summary to the terminal
- An Excel workbook: `aws_inventory.xlsx` with detailed inventory and a summary tab

## 📂 Output

- `aws_inventory.xlsx`  
  - `Summary` tab for account/region/service/count/capacity
  - One tab per service per account-region (e.g., `EC2_1234_useast1`)


---

## 📄 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 Brian Nelson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell   
copies of the Software, and to permit persons to whom the Software is       
furnished to do so, subject to the following conditions:                    

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.                             

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,   
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER     
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING    
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
```
