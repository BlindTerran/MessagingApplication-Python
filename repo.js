async function createArticle() {
    let title = document.getElementById('article_title').value;
    let content = document.getElementById('article_content').value;
    let response = await axios.post('/create_article', { title: title, content: content });
    if (response.data.success) {
        window.location.reload();
    } else {
        alert(response.data.error);
    }
}

async function editArticle(articleId) {
    let title = prompt('Enter new title:');
    let content = prompt('Enter new content:');
    let response = await axios.post('/edit_article', { article_id: articleId, title: title, content: content });
    if (response.data.success) {
        window.location.reload();
    } else {
        alert(response.data.error);
    }
}

async function deleteArticle(articleId) {
    let response = await axios.post('/delete_article', { article_id: articleId });
    if (response.data.success) {
        window.location.reload();
    } else {
        alert(response.data.error);
    }
}

async function addComment(articleId) {
    let content = document.getElementById('comment_content_' + articleId).value;
    let response = await axios.post('/add_comment', { article_id: articleId, content: content });
    if (response.data.success) {
        window.location.reload();
    } else {
        alert(response.data.error);
    }
}

async function deleteComment(commentId) {
    let response = await axios.post('/delete_comment', { comment_id: commentId });
    if (response.data.success) {
        window.location.reload();
    } else {
        alert(response.data.error);
    }
}