#!/bin/bash
# 记忆星河 MVP - GitHub推送脚本
# 请先确保已安装 gh CLI 并完成认证: gh auth login

REPO_NAME="memory-star-mvp"
REPO_DESC="AI辅助老年人回忆录撰写平台 - MVP版本"

echo "🚀 准备推送到GitHub..."

# 检查gh是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ 请先安装 GitHub CLI:"
    echo "   Ubuntu/Debian: sudo apt install gh"
    echo "   macOS: brew install gh"
    exit 1
fi

# 检查认证状态
if ! gh auth status &> /dev/null; then
    echo "❌ 请先登录GitHub:"
    echo "   gh auth login"
    exit 1
fi

# 创建仓库
echo "📦 创建GitHub仓库..."
gh repo create "$REPO_NAME" --public --description "$REPO_DESC" --source=. --remote=origin --push

echo "✅ 完成！"
echo ""
echo "仓库地址: https://github.com/$(gh api user -q .login)/$REPO_NAME"
