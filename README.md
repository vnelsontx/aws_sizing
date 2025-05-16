# AWS Org Inventory Script

This script collects inventory data across all accounts in an AWS Organization using a cross-account IAM role.

## Features
- EC2: Instance counts by region
- EFS: File system type and capacity
- RDS: Database type, engine, and allocated storage
- S3: Bucket name and region

## Requirements
- Python 3.8+
- Boto3
- IAM role (`OrganizationAccountAccessRole`) in each member account with read-only permissions

## Setup

1. Install dependencies:
    ```bash
    pip install boto3
    ```

2. Configure your AWS CLI with access to the management/delegated admin account.

3. Run the script:
    ```bash
    python aws_org_inventory.py
    ```

4. Output CSVs will be saved in the `inventory_output/` folder.
