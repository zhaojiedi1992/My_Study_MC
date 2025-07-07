/**
 * comment.js - 增强型评论系统 (Sphinx + ReadTheDocs + Utterances)
 * 功能特性:
 * - 支持文件上传
 * - 文件大小验证
 * - 文件类型验证
 * - 良好的浏览器兼容性
 * - 响应式设计
 * - 上传进度显示
 */

document.addEventListener('DOMContentLoaded', function() {
    // 配置项
    const CONFIG = {
        MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
        ALLOWED_FILE_TYPES: [
            'image/jpeg', 
            'image/png', 
            'image/gif',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ],
        UTTERANCES: {
            repo: 'zhaojiedi1992/My_Study_MC', // 在 Sphinx 的 conf.py 中设置
            issueTerm: 'pathname',
            theme: 'github-light'
        },
        TEXT: {
            title: '发表评论',
            placeholder: '请输入您的评论内容...',
            fileLabel: '附件上传 (可选，最大5MB):',
            submitBtn: '提交评论',
            fileTypeError: '文件类型不允许。允许的类型: ',
            fileSizeError: '文件过大 (最大 5MB)',
            submitSuccess: '评论已准备，请在下方Utterances评论框中提交',
            submitError: '错误: 无法连接到评论系统，请手动复制提交'
        }
    };

    // 主初始化函数
    function initEnhancedCommentSystem() {
        if (isUtterancesLoaded()) {
            setupCommentUI();
        } else {
            waitForUtterances(setupCommentUI);
        }
    }

    // 检查Utterances是否已加载
    function isUtterancesLoaded() {
        return typeof utterances !== 'undefined';
    }

    // 等待Utterances加载
    function waitForUtterances(callback) {
        const observer = new MutationObserver(function(mutations, observerInstance) {
            if (isUtterancesLoaded()) {
                callback();
                observerInstance.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 设置评论界面
    function setupCommentUI() {
        const utterancesContainer = document.querySelector('.utterances');
        if (!utterancesContainer) return;

        const commentContainer = createCommentContainer();
        const commentForm = createCommentForm();

        // 插入到页面中
        utterancesContainer.parentNode.insertBefore(commentContainer, utterancesContainer);
        commentContainer.appendChild(commentForm);

        // 添加事件监听
        setupEventListeners(commentForm);
    }

    // 创建评论容器
    function createCommentContainer() {
        const container = document.createElement('div');
        container.className = 'enhanced-comments-container';
        Object.assign(container.style, {
            margin: '20px 0',
            padding: '15px',
            borderRadius: '4px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #e1e4e8'
        });

        const title = document.createElement('h3');
        title.textContent = CONFIG.TEXT.title;
        title.style.marginTop = '0';
        container.appendChild(title);

        return container;
    }

    // 创建评论表单
    function createCommentForm() {
        const form = document.createElement('form');
        form.id = 'enhanced-comment-form';

        // 评论文本框
        form.appendChild(createTextarea());
        
        // 文件上传区域
        form.appendChild(createFileUploadSection());
        
        // 提交按钮
        form.appendChild(createSubmitButton());
        
        // 进度条
        form.appendChild(createProgressBar());

        return form;
    }

    // 创建文本输入框
    function createTextarea() {
        const textarea = document.createElement('textarea');
        textarea.id = 'comment-text';
        textarea.placeholder = CONFIG.TEXT.placeholder;
        textarea.required = true;
        Object.assign(textarea.style, {
            width: '100%',
            minHeight: '100px',
            marginBottom: '10px',
            padding: '8px',
            border: '1px solid #d1d5da',
            borderRadius: '3px'
        });
        return textarea;
    }

    // 创建文件上传区域
    function createFileUploadSection() {
        const section = document.createElement('div');
        section.style.margin = '10px 0';

        // 文件标签
        const label = document.createElement('label');
        label.textContent = CONFIG.TEXT.fileLabel;
        Object.assign(label.style, {
            display: 'block',
            marginBottom: '5px',
            fontWeight: 'bold'
        });
        section.appendChild(label);

        // 文件输入
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'comment-file';
        fileInput.name = 'comment-file';
        Object.assign(fileInput.style, {
            display: 'block',
            marginBottom: '5px'
        });
        section.appendChild(fileInput);

        // 文件信息显示
        const fileInfo = document.createElement('div');
        fileInfo.id = 'file-info';
        Object.assign(fileInfo.style, {
            fontSize: '0.8em',
            color: '#586069',
            marginBottom: '5px'
        });
        section.appendChild(fileInfo);

        // 错误信息显示
        const errorDisplay = document.createElement('div');
        errorDisplay.id = 'file-error';
        Object.assign(errorDisplay.style, {
            color: '#cb2431',
            fontSize: '0.8em',
            marginBottom: '10px',
            display: 'none'
        });
        section.appendChild(errorDisplay);

        return section;
    }

    // 创建提交按钮
    function createSubmitButton() {
        const button = document.createElement('button');
        button.type = 'submit';
        button.textContent = CONFIG.TEXT.submitBtn;
        Object.assign(button.style, {
            backgroundColor: '#2ea44f',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '3px',
            cursor: 'pointer',
            fontWeight: 'bold'
        });
        return button;
    }

    // 创建进度条
    function createProgressBar() {
        const container = document.createElement('div');
        container.id = 'upload-progress';
        container.style.display = 'none';
        container.style.marginTop = '10px';
        container.style.height = '5px';
        container.style.backgroundColor = '#e1e4e8';
        container.style.borderRadius = '3px';
        
        const bar = document.createElement('div');
        bar.id = 'progress-bar';
        bar.style.height = '100%';
        bar.style.width = '0%';
        bar.style.backgroundColor = '#2ea44f';
        bar.style.borderRadius = '3px';
        bar.style.transition = 'width 0.3s ease';
        
        container.appendChild(bar);
        return container;
    }

    // 设置事件监听
    function setupEventListeners(form) {
        const fileInput = form.querySelector('#comment-file');
        fileInput.addEventListener('change', handleFileSelect);
        
        form.addEventListener('submit', handleFormSubmit);
    }

    // 处理文件选择
    function handleFileSelect(event) {
        const file = event.target.files[0];
        const errorElement = document.getElementById('file-error');
        errorElement.style.display = 'none';
        errorElement.textContent = '';
        
        if (!file) {
            document.getElementById('file-info').textContent = '';
            return;
        }

        // 验证文件大小
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            errorElement.textContent = CONFIG.TEXT.fileSizeError + 
                formatFileSize(CONFIG.MAX_FILE_SIZE) + ')';
            errorElement.style.display = 'block';
            event.target.value = '';
            document.getElementById('file-info').textContent = '';
            return;
        }

        // 验证文件类型
        if (CONFIG.ALLOWED_FILE_TYPES.indexOf(file.type) === -1) {
            errorElement.textContent = CONFIG.TEXT.fileTypeError + 
                CONFIG.ALLOWED_FILE_TYPES.join(', ');
            errorElement.style.display = 'block';
            event.target.value = '';
            document.getElementById('file-info').textContent = '';
            return;
        }

        // 显示文件信息
        document.getElementById('file-info').textContent = 
            `已选择: ${file.name} (${formatFileSize(file.size)})`;
    }

    // 处理表单提交
    function handleFormSubmit(event) {
        event.preventDefault();
        
        const commentText = document.getElementById('comment-text').value.trim();
        if (!commentText) {
            alert('请输入评论内容');
            return;
        }

        const fileInput = document.getElementById('comment-file');
        const file = fileInput.files[0];
        
        // 显示进度条
        document.getElementById('upload-progress').style.display = 'block';
        document.getElementById('progress-bar').style.width = '0%';
        
        if (file) {
            // 模拟文件上传 (实际使用时替换为真实上传逻辑)
            simulateFileUpload(file, function(uploadedFileUrl) {
                // 在评论中包含文件信息
                const fullComment = `${commentText}\n\n[附件: ${file.name}](${uploadedFileUrl})`;
                postCommentToUtterances(fullComment);
            });
        } else {
            // 没有附件，直接提交评论
            postCommentToUtterances(commentText);
        }
    }

    // 模拟文件上传
    function simulateFileUpload(file, callback) {
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += Math.random() * 10;
            if (progress > 100) progress = 100;
            document.getElementById('progress-bar').style.width = `${progress}%`;
            
            if (progress === 100) {
                clearInterval(progressInterval);
                setTimeout(function() {
                    // 实际应用中替换为真实的上传逻辑
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        callback(e.target.result); // 返回数据URL
                    };
                    reader.readAsDataURL(file);
                }, 500);
            }
        }, 200);
    }

    // 提交评论到Utterances
    function postCommentToUtterances(commentText) {
        const utterancesFrame = document.querySelector('.utterances-frame');
        
        if (utterancesFrame && utterancesFrame.contentWindow) {
            // 尝试预填充评论框
            utterancesFrame.contentWindow.postMessage({
                type: 'set-comment',
                value: commentText
            }, 'https://utteranc.es');
            
            // 聚焦评论框
            utterancesFrame.contentWindow.postMessage({
                type: 'focus-comment'
            }, 'https://utteranc.es');
            
            // 提示用户手动提交
            alert(CONFIG.TEXT.submitSuccess);
        } else {
            // 出错处理
            alert(CONFIG.TEXT.submitError);
            console.log('评论内容:', commentText);
        }
        
        // 重置表单
        resetCommentForm();
    }

    // 重置评论表单
    function resetCommentForm() {
        document.getElementById('comment-text').value = '';
        document.getElementById('comment-file').value = '';
        document.getElementById('file-info').textContent = '';
        document.getElementById('upload-progress').style.display = 'none';
    }

    // 格式化文件大小
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 启动评论系统
    initEnhancedCommentSystem();
});