import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [posts, setPosts] = useState([]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // 发帖状态
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  
  // 视图控制与当前帖子状态
  const [currentView, setCurrentView] = useState('list'); // 'list', 'newPost', 'detail'
  const [activePost, setActivePost] = useState(null); // 存储当前正在查看的完整帖子
  
  // 评论状态
  const [commentContent, setCommentContent] = useState('');
  const [replyToId, setReplyToId] = useState(null); // 用于记录正在回复哪条评论

  // 🛠️ 抽取退出登录逻辑（一处编写，多处复用）
  const handleLogout = (isExpired = false) => {
    setToken('');
    localStorage.removeItem('token');
    if (isExpired) {
      alert('您的登录已过期，请重新登录！');
    } else {
      alert('已退出登录');
    }
    setCurrentView('list'); // 退出后切回列表主页
  };

  // 获取帖子列表
  const fetchPosts = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/posts`);
      const data = await res.json();
      setPosts(data);
    } catch (err) {
      console.error('获取帖子失败', err);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  // 登录
  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      formData.append('grant_type', 'password');

      const res = await fetch(`${API_BASE}/auth/access-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
      
      const data = await res.json();
      if (data.access_token) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        alert('登录成功！');
        // 登录成功清空输入框
        setEmail('');
        setPassword('');
      } else {
        alert('登录失败：' + JSON.stringify(data));
      }
    } catch (err) {
      alert('登录出错：' + err.message);
    }
  };

  // 注册
  const handleRegister = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (res.status === 201) {
        alert('注册成功！请登录');
      } else {
        const data = await res.json();
        alert('注册失败：' + JSON.stringify(data));
      }
    } catch (err) {
      alert('注册出错：' + err.message);
    }
  };

  // 发帖
  const handleCreatePost = async () => {
    if (!token) { alert('请先登录'); return; }
    if (!title.trim() || !content.trim()) { alert('标题和内容不能为空！'); return; }

    try {
      const res = await fetch(`${API_BASE}/api/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title, content })
      });
      
      if (res.status === 401) {
        handleLogout(true);
        return;
      }

      if (res.status === 201) {
        alert('发布成功！');
        setTitle('');
        setContent('');
        fetchPosts();
        setCurrentView('list'); 
      } else {
        const errorData = await res.json();
        alert(`发布失败，后端返回：${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      alert('发帖网络出错：' + err.message);
    }
  };

  // 查看帖子详情
  const viewPostDetail = async (postId) => {
    try {
      const res = await fetch(`${API_BASE}/api/posts/${postId}`);
      const data = await res.json();
      setActivePost(data);
      setCurrentView('detail');
      setReplyToId(null); 
    } catch (err) {
      alert('获取详情失败');
    }
  };

  // 发送评论
  const handleComment = async () => {
    if (!token) { alert('请先登录'); return; }
    if (!commentContent.trim()) { alert('评论不能为空'); return; }
    
    const payload = { content: commentContent };
    if (replyToId) {
      payload.parent_id = replyToId;
    }

    try {
      const res = await fetch(`${API_BASE}/api/comments?post_id=${activePost.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.status === 401) {
        handleLogout(true);
        return;
      }

      if (res.status === 201) {
        setCommentContent('');
        setReplyToId(null);
        viewPostDetail(activePost.id);
      } else {
        const errorData = await res.json();
        alert(`评论失败，后端返回：${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      alert('评论网络出错：' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-800">
      {/* 顶部导航 */}
      <div className="bg-pink-500 text-white p-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-bold cursor-pointer" onClick={() => setCurrentView('list')}>
          Mothertalktome
        </h1>
        {token ? (
          <div className="flex items-center gap-3">
            <span className="bg-pink-600 px-3 py-1 rounded-full text-xs font-semibold">已登录</span>
            {/* 新增退出登录按钮 */}
            <button 
              onClick={() => handleLogout(false)} 
              className="bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-xs font-medium transition shadow-sm"
            >
              退出登录
            </button>
          </div>
        ) : (
          <span className="text-sm bg-pink-600 px-3 py-1 rounded-full text-xs">未登录</span>
        )}
      </div>

      <div className="max-w-3xl mx-auto p-4 mt-4">
        
        {/* 未登录时显示登录框 */}
        {!token && (
          <div className="bg-white p-6 rounded-lg shadow-sm mb-6 border border-gray-200">
            <h2 className="text-lg font-bold mb-4 text-gray-700">认证 (请重新登录以刷新令牌)</h2>
            <div className="flex gap-2 mb-3">
              <input type="email" placeholder="邮箱" className="border p-2 rounded w-full outline-none focus:border-pink-400" value={email} onChange={(e) => setEmail(e.target.value)} />
              <input type="password" placeholder="密码" className="border p-2 rounded w-full outline-none focus:border-pink-400" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <button onClick={handleLogin} className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2 rounded font-semibold transition shadow-sm">登录</button>
              <button onClick={handleRegister} className="bg-green-500 hover:bg-green-600 text-white px-5 py-2 rounded font-semibold transition shadow-sm">注册</button>
            </div>
          </div>
        )}

        {/* 导航按钮 */}
        {currentView !== 'detail' && (
          <div className="flex gap-4 mb-6">
            <button 
              className={`font-bold pb-2 transition ${currentView === 'list' ? 'text-pink-600 border-b-2 border-pink-600' : 'text-gray-400'}`}
              onClick={() => setCurrentView('list')}
            >
              最新动态
            </button>
            <button 
              className={`font-bold pb-2 transition ${currentView === 'newPost' ? 'text-pink-600 border-b-2 border-pink-600' : 'text-gray-400'}`}
              onClick={() => setCurrentView('newPost')}
            >
              发布新帖
            </button>
          </div>
        )}

        {/* 视图 1: 帖子列表 */}
        {currentView === 'list' && (
          <div className="space-y-4">
            {posts.map(post => (
              <div 
                key={post.id} 
                className="bg-white p-5 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer border border-gray-100 hover:border-pink-200"
                onClick={() => viewPostDetail(post.id)}
              >
                <h3 className="font-bold text-xl text-gray-800">{post.title}</h3>
                <p className="text-gray-600 mt-2 line-clamp-2">{post.content}</p>
                <div className="text-sm text-gray-400 mt-4 flex gap-4">
                  <span>发布于 {new Date(post.created_at).toLocaleString()}</span>
                  <span className="text-pink-500 flex items-center gap-1 font-medium">
                    💬 {post.comments?.length || 0} 条评论
                  </span>
                </div>
              </div>
            ))}
            {posts.length === 0 && <p className="text-center text-gray-400 py-10">暂无动态，快去发布第一条吧！</p>}
          </div>
        )}

        {/* 视图 2: 发布新帖 */}
        {currentView === 'newPost' && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <input type="text" placeholder="给帖子起个标题吧..." className="border p-3 rounded w-full mb-4 text-lg font-semibold outline-none focus:border-pink-400" value={title} onChange={(e) => setTitle(e.target.value)} />
            <textarea placeholder="分享你的想法，输入 @Mother 召唤AI..." rows="6" className="border p-3 rounded w-full mb-4 outline-none focus:border-pink-400 resize-none leading-relaxed" value={content} onChange={(e) => setContent(e.target.value)} />
            <button onClick={handleCreatePost} className="bg-pink-500 hover:bg-pink-600 text-white font-bold px-6 py-2 rounded-full transition w-full shadow-sm">发布帖子</button>
          </div>
        )}

        {/* 视图 3: 帖子详情页 */}
        {currentView === 'detail' && activePost && (
          <div>
            <button onClick={() => setCurrentView('list')} className="text-pink-500 mb-4 font-semibold flex items-center gap-1 hover:text-pink-600">
              ← 返回列表
            </button>
            
            {/* 帖子主内容 */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{activePost.title}</h2>
              <p className="text-gray-700 text-lg leading-relaxed whitespace-pre-wrap">{activePost.content}</p>
              <div className="text-sm text-gray-400 mt-6 pt-4 border-t border-gray-100">
                发布于 {new Date(activePost.created_at).toLocaleString()}
              </div>
            </div>

            {/* 评论区 */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="font-bold text-lg mb-6 border-b pb-2 text-gray-700">评论区 ({activePost.comments?.length || 0})</h3>
              
              {/* 评论列表 */}
              <div className="space-y-4 mb-8">
                {activePost.comments?.map(comment => (
                  <div key={comment.id} className={`p-4 rounded-lg transition ${comment.is_ai ? 'bg-pink-50 border border-pink-100 shadow-sm' : 'bg-gray-50'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <span className={`font-bold text-sm ${comment.is_ai ? 'text-pink-600' : 'text-blue-600'}`}>
                        {comment.is_ai ? 'AI' : '用户'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">{comment.content}</p>
                    
                    {/* 嵌套回复按钮 */}
                    {!comment.is_ai && (
                      <button 
                        onClick={() => setReplyToId(comment.id)}
                        className="text-xs text-pink-500 mt-2 hover:text-pink-600 font-semibold transition"
                      >
                        回复此条
                      </button>
                    )}
                  </div>
                ))}
                {activePost.comments?.length === 0 && <p className="text-center text-gray-400 text-sm py-4">还没有评论，快来聊聊吧...</p>}
              </div>

              {/* 发布评论框 */}
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                {replyToId && (
                  <div className="flex justify-between items-center mb-2 bg-pink-100 px-3 py-1 rounded text-sm text-pink-700 font-medium animate-pulse">
                    <span>正在回复特定的评论...</span>
                    <button onClick={() => setReplyToId(null)} className="text-red-500 hover:text-red-700 font-bold">✕ 取消</button>
                  </div>
                )}
                <p className="text-xs text-pink-500 mb-2 font-semibold">提示：在内容中包含 @Mother 即可召唤 AI 自动回复</p>
                <textarea
                  placeholder="写下你的评论..."
                  rows="3"
                  className="border border-gray-300 p-3 rounded w-full mb-3 outline-none focus:border-pink-400 focus:ring-1 focus:ring-pink-400 transition bg-white resize-none"
                  value={commentContent}
                  onChange={(e) => setCommentContent(e.target.value)}
                />
                <div className="flex justify-end">
                  <button onClick={handleComment} className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-full font-bold transition shadow-sm">
                    发送评论
                  </button>
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;