document.addEventListener('DOMContentLoaded', function() {
    const REPO = 'zhaojiedi1992/MY_STUDY_MC';
    const THEME = 'github-light';
    
    // 1. 创建容器和上传按钮
    const container = document.createElement('div');
    container.id = 'utterances-comments';
    container.style.position = 'relative';
    
    const uploadBtn = document.createElement('button');
    uploadBtn.textContent = '🖼️ 上传图片';
    uploadBtn.style.cssText = `
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
    container.appendChild(uploadBtn);

    // 2. 插入容器到页面
    const content = document.querySelector('.document') || document.querySelector('.body');
    if (content) content.appendChild(container);

    // 3. 初始化Utterances（新增回调函数）
    const script = document.createElement('script');
    script.src = 'https://utteranc.es/client.js';
    script.setAttribute('repo', REPO);
    script.setAttribute('issue-term', 'pathname');
    script.setAttribute('theme', THEME);
    script.setAttribute('crossorigin', 'anonymous');
    script.async = true;
    
    // 4. 监听Utterances加载完成事件（关键修复！）
    script.onload = function() {
        // 等待Utterances完全初始化
        const checkInterval = setInterval(() => {
            if (window.utterances?.issueNumber) {
                clearInterval(checkInterval);
                initUploadButton(); // 安全初始化按钮
            }
        }, 500);
    };
    container.appendChild(script);

    // 5. 安全的按钮初始化（仅在Utterances就绪后调用）
    function initUploadButton() {
        uploadBtn.onclick = async function() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                
                if (file.size > 10 * 1024 * 1024) {
                    alert('图片大小不能超过10MB');
                    return;
                }

                uploadBtn.textContent = '⏳ 上传中...';
                uploadBtn.disabled = true;

                try {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const markdownImg = `![图片](${e.target.result})`;
                        navigator.clipboard.writeText(markdownImg).then(() => {
                            alert('✅ 图片链接已复制到剪贴板\n请粘贴到评论框中');
                        });
                    };
                    reader.readAsDataURL(file);
                } catch (error) {
                    alert('⚠️ 上传失败: ' + error.message);
                } finally {
                    uploadBtn.textContent = '🖼️ 上传图片';
                    uploadBtn.disabled = false;
                }
            };
            input.click();
        };
    }
});