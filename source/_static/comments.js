/**
 * Utterances评论系统 + 图片上传功能
 * 完整功能版本 v1.2
 * 特性：
 * 1. 可靠的Utterances加载检测机制
 * 2. 图片上传+Markdown生成
 * 3. 自动粘贴到剪贴板
 * 4. 全面的错误处理
 * 5. 移动端适配
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== 配置区域 ====================
    const CONFIG = {
        REPO: 'zhaojiedi1992/MY_STUDY_MC',  // 格式: 用户名/仓库名
        THEME: 'github-light',              // 主题: github-light/github-dark等
        MAX_IMAGE_SIZE: 10 * 1024 * 1024,   // 最大图片大小(10MB)
        ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    };

    // ==================== 初始化 ====================
    console.log('[Comments] 初始化评论系统...');
    
    // 1. 创建容器
    const container = document.createElement('div');
    container.id = 'utterances-container';
    container.style.position = 'relative';
    container.style.margin = '40px 0';
    container.style.minHeight = '200px';  // 预留加载高度

    // 2. 创建控制面板
    const panel = document.createElement('div');
    panel.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding: 10px;
        background: #f6f8fa;
        border-radius: 6px;
        border: 1px solid #e1e4e8;
    `;

    // 3. 添加功能按钮
    const uploadBtn = createButton('🖼️ 上传图片', 'primary');
    const refreshBtn = createButton('🔄 刷新评论', 'secondary');
    
    uploadBtn.style.marginRight = '8px';
    panel.append(uploadBtn, refreshBtn);
    container.appendChild(panel);

    // 4. 插入到页面
    const content = document.querySelector('.document') || 
                   document.querySelector('.content') || 
                   document.querySelector('body');
    content?.appendChild(container);

    // ==================== Utterances加载 ====================
    let utterancesLoaded = false;
    loadUtterances();

    // ==================== 事件监听 ====================
    uploadBtn.addEventListener('click', handleUpload);
    refreshBtn.addEventListener('click', () => {
        if (utterancesLoaded) {
            window.utterances?.refresh();
            showToast('评论已刷新');
        } else {
            loadUtterances(true);
        }
    });

    // ==================== 核心函数 ====================
    function loadUtterances(force = false) {
        if (window.utterances && !force) return;

        // 清理旧脚本
        document.querySelector('#utterances-container script')?.remove();
        
        const script = document.createElement('script');
        script.src = `https://utteranc.es/client.js?ts=${Date.now()}`;
        script.setAttribute('repo', CONFIG.REPO);
        script.setAttribute('issue-term', 'pathname');
        script.setAttribute('theme', CONFIG.THEME);
        script.setAttribute('crossorigin', 'anonymous');
        script.async = true;

        script.onload = () => {
            console.log('[Comments] Utterances脚本加载完成');
            checkUtterancesReady();
        };

        script.onerror = () => {
            console.error('[Comments] Utterances加载失败');
            showError('评论系统加载失败，请检查网络或仓库配置');
        };

        container.appendChild(script);
    }

    function checkUtterancesReady() {
        const maxAttempts = 10;
        let attempts = 0;

        const checkInterval = setInterval(() => {
            attempts++;
            const iframe = container.querySelector('iframe');
            
            if (iframe) {
                if (iframe.contentDocument?.readyState === 'complete') {
                    clearInterval(checkInterval);
                    utterancesLoaded = true;
                    console.log('[Comments] Utterances完全就绪');
                    showToast('评论系统已就绪', 'success');
                }
            }

            if (attempts >= maxAttempts) {
                clearInterval(checkInterval);
                console.warn('[Comments] Utterances加载超时');
                showError('评论加载超时，请尝试手动刷新');
            }
        }, 500);
    }

    async function handleUpload() {
        if (!utterancesLoaded) {
            showError('请等待评论系统初始化完成');
            return;
        }

        try {
            // 检查权限
            const permission = await navigator.permissions.query({ name: 'clipboard-write' });
            if (permission.state !== 'granted') {
                throw new Error('缺少剪贴板写入权限');
            }

            // 创建文件输入
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = CONFIG.ALLOWED_TYPES.join(',');
            input.style.display = 'none';

            input.onchange = async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;

                // 验证文件
                if (!CONFIG.ALLOWED_TYPES.includes(file.type)) {
                    throw new Error(`仅支持 ${CONFIG.ALLOWED_TYPES.map(t => t.split('/')[1]).join('/')} 格式`);
                }

                if (file.size > CONFIG.MAX_IMAGE_SIZE) {
                    throw new Error(`图片大小不能超过 ${CONFIG.MAX_IMAGE_SIZE / 1024 / 1024}MB`);
                }

                // 上传处理
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '⏳ 上传中...';
                
                const markdown = await processImage(file);
                await navigator.clipboard.writeText(markdown);
                
                showToast('✅ Markdown图片链接已复制到剪贴板', 'success', 5000);
                focusCommentTextarea();
            };

            document.body.appendChild(input);
            input.click();
            setTimeout(() => input.remove(), 1000);
        } catch (error) {
            console.error('[Upload Error]', error);
            showError(`上传失败: ${error.message}`);
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '🖼️ 上传图片';
        }
    }

    function processImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const dataUrl = e.target.result;
                resolve(`![${file.name}](${dataUrl})`);
            };
            
            reader.onerror = () => reject(new Error('文件读取失败'));
            reader.readAsDataURL(file);
        });
    }

    function focusCommentTextarea() {
        const iframe = container.querySelector('iframe');
        if (!iframe) return;
        
        try {
            const textarea = iframe.contentDocument?.querySelector('textarea[aria-label="Comment body"]');
            textarea?.focus();
        } catch (e) {
            console.warn('[Comments] 无法聚焦评论框:', e);
        }
    }

    // ==================== UI组件 ====================
    function createButton(text, type = 'primary') {
        const btn = document.createElement('button');
        btn.innerHTML = text;
        btn.style.cssText = `
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            border: 1px solid ${type === 'primary' ? '#d1d5da' : '#e1e4e8'};
            background: ${type === 'primary' ? '#f6f8fa' : '#ffffff'};
            transition: all 0.2s;
        `;
        
        btn.onmouseover = () => btn.style.backgroundColor = type === 'primary' ? '#eaecef' : '#f6f8fa';
        btn.onmouseout = () => btn.style.backgroundColor = type === 'primary' ? '#f6f8fa' : '#ffffff';
        
        return btn;
    }

    function showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#28a745' : '#0366d6'};
            color: white;
            border-radius: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            animation: fadeIn 0.3s;
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    function showError(message) {
        const errorBox = document.createElement('div');
        errorBox.textContent = message;
        errorBox.style.cssText = `
            padding: 10px;
            margin-top: 10px;
            background: #ffeef0;
            border: 1px solid #ffdce0;
            border-radius: 6px;
            color: #d73a49;
            font-size: 14px;
        `;
        
        panel.appendChild(errorBox);
        setTimeout(() => errorBox.remove(), 5000);
    }
});

// 添加必要CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(10px); }
    }
    #utterances-container iframe {
        width: 100%;
        min-height: 150px;
        border: none;
    }
`;
document.head.appendChild(style);