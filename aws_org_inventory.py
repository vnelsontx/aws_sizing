
import boto3
from botocore.exceptions import ClientError
from collections import defaultdict
import csv
from pathlib import Path
import json

# Configuration
ROLE_NAME = "OrganizationAccountAccessRole"
REGIONS = ['us-east-1', 'us-west-2']  # Add more regions as needed

org_client = boto3.client('organizations')
sts_client = boto3.client('sts')

accounts = org_client.list_accounts()['Accounts']
results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # results[account_id][region][service] = data

def assume_role(account_id):
    try:
        response = sts_client.assume_role(
            RoleArn=f"arn:aws:iam::{account_id}:role/{ROLE_NAME}",
            RoleSessionName="InventorySession"
        )
        creds = response['Credentials']
        return dict(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        )
    except ClientError as e:
        print(f"[!] Failed to assume role in {account_id}: {e}")
        return None

def collect_inventory(account_id, creds):
    for region in REGIONS:
        # --- EC2 ---
        try:
            ec2 = boto3.client('ec2', region_name=region, **creds)
            instances = ec2.describe_instances()
            ec2_count = sum(len(r['Instances']) for r in instances['Reservations'])
            results[account_id][region]['EC2'] = {"VM_Count": ec2_count}
        except Exception as e:
            results[account_id][region]['EC2'] = {"error": str(e)}

        # --- EFS ---
        try:
            efs = boto3.client('efs', region_name=region, **creds)
            filesystems = efs.describe_file_systems()
            efs_summary = []
            for fs in filesystems['FileSystems']:
                efs_summary.append({
                    "ID": fs['FileSystemId'],
                    "Type": fs['PerformanceMode'],
                    "Size_GB": fs.get("SizeInBytes", {}).get("Value", 0) / 1024**3
                })
            results[account_id][region]['EFS'] = efs_summary
        except Exception as e:
            results[account_id][region]['EFS'] = {"error": str(e)}

        # --- RDS ---
        try:
            rds = boto3.client('rds', region_name=region, **creds)
            dbs = rds.describe_db_instances()
            rds_summary = []
            for db in dbs['DBInstances']:
                rds_summary.append({
                    "DBIdentifier": db['DBInstanceIdentifier'],
                    "Class": db['DBInstanceClass'],
                    "Allocated_Storage_GB": db['AllocatedStorage'],
                    "Engine": db['Engine']
                })
            results[account_id][region]['RDS'] = rds_summary
        except Exception as e:
            results[account_id][region]['RDS'] = {"error": str(e)}

        # --- S3 (Run only once per account, not per region) ---
        if region == REGIONS[0]:
            try:
                s3 = boto3.client('s3', **creds)
                buckets = s3.list_buckets()['Buckets']
                bucket_summary = []
                for bucket in buckets:
                    name = bucket['Name']
                    try:
                        loc = s3.get_bucket_location(Bucket=name)['LocationConstraint'] or 'us-east-1'
                        bucket_summary.append({"Name": name, "Region": loc})
                    except:
                        bucket_summary.append({"Name": name, "Region": "unknown"})
                results[account_id]['global']['S3'] = bucket_summary
            except Exception as e:
                results[account_id]['global']['S3'] = {"error": str(e)}

def export_to_csv(results, output_dir="inventory_output"):
    Path(output_dir).mkdir(exist_ok=True)

    ec2_rows = []
    efs_rows = []
    rds_rows = []
    s3_rows = []

    for account_id, regions in results.items():
        for region, services in regions.items():
            # EC2
            if 'EC2' in services and isinstance(services['EC2'], dict):
                ec2_data = services['EC2']
                ec2_rows.append({
                    "Account ID": account_id,
                    "Region": region,
                    "VM Count": ec2_data.get("VM_Count", "N/A"),
                    "Error": ec2_data.get("error", "")
                })

            # EFS
            if 'EFS' in services and isinstance(services['EFS'], list):
                for fs in services['EFS']:
                    efs_rows.append({
                        "Account ID": account_id,
                        "Region": region,
                        "FileSystem ID": fs.get("ID", ""),
                        "Type": fs.get("Type", ""),
                        "Size (GB)": round(fs.get("Size_GB", 0), 2)
                    })

            # RDS
            if 'RDS' in services and isinstance(services['RDS'], list):
                for db in services['RDS']:
                    rds_rows.append({
                        "Account ID": account_id,
                        "Region": region,
                        "DB Identifier": db.get("DBIdentifier", ""),
                        "Class": db.get("Class", ""),
                        "Engine": db.get("Engine", ""),
                        "Allocated Storage (GB)": db.get("Allocated_Storage_GB", "")
                    })

            # S3
            if region == 'global' and 'S3' in services and isinstance(services['S3'], list):
                for bucket in services['S3']:
                    s3_rows.append({
                        "Account ID": account_id,
                        "Bucket Name": bucket.get("Name", ""),
                        "Region": bucket.get("Region", "")
                    })

    # Write CSVs
    with open(f"{output_dir}/ec2_inventory.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Account ID", "Region", "VM Count", "Error"])
        writer.writeheader()
        writer.writerows(ec2_rows)

    with open(f"{output_dir}/efs_inventory.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Account ID", "Region", "FileSystem ID", "Type", "Size (GB)"])
        writer.writeheader()
        writer.writerows(efs_rows)

    with open(f"{output_dir}/rds_inventory.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Account ID", "Region", "DB Identifier", "Class", "Engine", "Allocated Storage (GB)"])
        writer.writeheader()
        writer.writerows(rds_rows)

    with open(f"{output_dir}/s3_inventory.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Account ID", "Bucket Name", "Region"])
        writer.writeheader()
        writer.writerows(s3_rows)

    print(f"\n✅ CSV export complete: {output_dir}/")

# === Run the Org-Wide Inventory ===
print(f"🔍 Starting inventory across {len(accounts)} accounts...\n")

for acct in accounts:
    account_id = acct['Id']
    if acct['Status'] != 'ACTIVE':
        continue
    print(f"→ Collecting from Account: {account_id}")
    creds = assume_role(account_id)
    if creds:
        collect_inventory(account_id, creds)

# Output JSON and CSVs
print(json.dumps(results, indent=2))
export_to_csv(results)
