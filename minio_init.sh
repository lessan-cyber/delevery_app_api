#!/bin/bash

set -e


# Création du bucket
mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc mb local/gozem || echo "Bucket already exists"

# Appliquer la politique publique pour le bucket
mc anonymous set download local/gozem || echo "Policy already applied"

# Appliquer une politique spécifique pour le contrôle en écriture/lecture
cat <<EOF > /tmp/policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::gozem/*"]
    },
    {
      "Effect": "Deny",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::gozem/*"]
    }
  ]
}
EOF
mc admin policy set local gozem-read-only /tmp/policy.json
mc admin policy attach local gozem-read-only --bucket gozem || echo "Policy already attached"
