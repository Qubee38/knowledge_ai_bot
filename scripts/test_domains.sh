#!/bin/bash
# ドメイン管理API完全テスト

echo "======================================"
echo "Domain Management API Test"
echo "======================================"

# 1. ログイン
echo ""
echo "1. Login..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test1234"
  }' | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Login failed"
    exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."

# 2. ドメイン一覧（申請前）
echo ""
echo "2. Get domains (before request)..."
curl -s http://localhost:8000/api/domains \
  -H "Authorization: Bearer $TOKEN" | jq '.domains[0].access_status'

# 3. ドメインアクセス申請
echo ""
echo "3. Request domain access..."
ACCESS_ID=$(curl -s -X POST http://localhost:8000/api/domains/horse-racing/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "競馬分析に興味があります"}' | jq -r '.access_id')

if [ -z "$ACCESS_ID" ] || [ "$ACCESS_ID" = "null" ]; then
    echo "⚠️  Domain access already exists or failed"
else
    echo "✅ Domain access granted: $ACCESS_ID"
fi

# 4. ドメイン一覧（申請後）
echo ""
echo "4. Get domains (after request)..."
curl -s http://localhost:8000/api/domains \
  -H "Authorization: Bearer $TOKEN" | jq '.domains[0] | {access_status, requested_at}'

# 5. アクセス権確認
echo ""
echo "5. Check access..."
curl -s http://localhost:8000/api/domains/check-access/horse-racing \
  -H "Authorization: Bearer $TOKEN" | jq

# 6. 重複申請テスト
echo ""
echo "6. Test duplicate request..."
curl -s -X POST http://localhost:8000/api/domains/horse-racing/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "再申請"}' | jq '.detail'

# 7. アクセス取り消し（オプション）
read -p "Do you want to revoke access? (y/n): " REVOKE

if [ "$REVOKE" = "y" ]; then
    echo ""
    echo "7. Revoke access..."
    curl -s -X DELETE http://localhost:8000/api/domains/horse-racing/access \
      -H "Authorization: Bearer $TOKEN" | jq
    
    echo ""
    echo "8. Get domains (after revoke)..."
    curl -s http://localhost:8000/api/domains \
      -H "Authorization: Bearer $TOKEN" | jq '.domains[0].access_status'
fi

echo ""
echo "======================================"
echo "✅ All tests completed!"
echo "======================================"