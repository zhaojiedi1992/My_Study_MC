// _static/comments.js - 增强版（支持图片上传）
document.addEventListener('DOMContentLoaded', function() {
    // ================= 基础配置 =================
    const REPO = 'zhaojiedi1992/MY_STUDY_MC'; // 替换为你的仓库
    const THEME = 'github-light';
    
    // ================= 1. 初始化Utterances =================
    const script = document.createElement('script');
    script.src = 'https://utteranc.es/client.js';
    script.setAttribute('repo', REPO);
    script.setAttribute('issue-term', 'pathname');
    script.setAttribute('theme', THEME);
    script.setAttribute('crossorigin', 'anonymous');
    script.async = true;

    // ================= 2. 创建评论容器 =================
    const container = document.createElement('div');
    container.id = 'utterances-comments';
    container.style.position = 'relative'; // 为上传按钮定位

    // ================= 3. 图片上传功能 =================
    const uploadBtn = document.createElement('button');
    uploadBtn.textContent = '🖼️ 上传图片';
    uploadBtn.style = `
        position: absolute;
        top: -40px;
        right: 0;
        padding: 5px 10px;
        background: #f6f8fa;
        border: 1px solid #d1d5da;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
    `;
    uploadBtn.onclick = handleImageUpload;

    // ================= 4. 插入DOM元素 =================
    const content = document.querySelector('.document') || document.querySelector('.body');
    if (content) {
        container.appendChild(uploadBtn);
        content.appendChild(container);
        container.appendChild(script);
    }

    // ================= 5. 图片上传处理函数 =================
    async function handleImageUpload() {
        // 5.1 创建文件选择器
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.display = 'none';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // 5.2 验证文件大小
            if (file.size > 10 * 1024 * 1024) {
                alert('图片大小不能超过10MB');
                return;
            }

            // 5.3 显示上传状态
            uploadBtn.textContent = '⏳ 上传中...';
            uploadBtn.disabled = true;

            try {
                // 5.4 获取当前Issue编号（通过Utterances全局变量）
                const issueNumber = window.utterances?.issueNumber;
                if (!issueNumber) throw new Error('未找到评论区');

                // 5.5 读取文件为Base64
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const base64Data = e.target.result.split(',')[1];
                    const markdownImg = `![图片](${e.target.result})`;

                    // 5.6 复制到剪贴板（让用户手动粘贴）
                    await navigator.clipboard.writeText(markdownImg);
                    alert('✅ 图片链接已复制到剪贴板\n请直接粘贴到评论框中');
                };
                reader.readAsDataURL(file);

            } catch (error) {
                console.error('上传失败:', error);
                alert('⚠️ 上传失败: ' + error.message);
            } finally {
                uploadBtn.textContent = '🖼️ 上传图片';
                uploadBtn.disabled = false;
            }
        };

        document.body.appendChild(input);
        input.click();
        input.remove();
    }
});