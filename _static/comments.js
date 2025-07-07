// Utterances 配置（需替换YOUR_*为实际值）
document.addEventListener('DOMContentLoaded', function() {
    const script = document.createElement('script');
    script.src = 'https://utteranc.es/client.js';
    script.setAttribute('repo', 'zhaojiedi1992/MY_STUDY_MC');
    script.setAttribute('issue-term', 'pathname');
    script.setAttribute('theme', 'github-light');
    script.setAttribute('crossorigin', 'anonymous');
    script.async = true;
    
    // 将评论容器插入到每个页面
    const container = document.createElement('div');
    container.id = 'utterances-comments';
    const content = document.querySelector('.document') || document.querySelector('.body');
    if (content) {
        content.appendChild(container);
        container.appendChild(script);
    }
});