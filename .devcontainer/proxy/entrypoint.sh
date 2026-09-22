#!/bin/sh
set -eu

# 空行・コメント・CRLF を除去する。ファイルが読めない場合は起動を中止する。
for list in whitelist blacklist; do
    awk '{ sub(/#.*/, ""); gsub(/^[[:space:]]+|[[:space:]]+$/, ""); if (length) print }' \
        "/etc/squid/lists/$list.txt" > "/tmp/$list.txt"
done

# 空の許可リストは制限なし。両方に一致した場合は拒否を優先する。
{
    if [ -s /tmp/blacklist.txt ]; then
        printf '%s\n' 'acl blocked_domains dstdomain -n "/tmp/blacklist.txt"' \
            'http_access deny blocked_domains'
    fi
    if [ -s /tmp/whitelist.txt ]; then
        printf '%s\n' 'acl allowed_domains dstdomain -n "/tmp/whitelist.txt"' \
            'http_access deny !allowed_domains'
    fi
} > /tmp/domain-access.conf

exec "$@"
