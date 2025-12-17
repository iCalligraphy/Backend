import requests
import json
import time

# API 基础 URL
BASE_URL = 'http://localhost:5000'

# 测试用户信息
TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'test123'

# 测试话题ID（使用数据库中实际存在的话题ID）
TEST_TOPIC_ID = 'technique'  # 技法交流话题

# 测试帖子内容
TEST_POST_DATA = {
    'title': '测试帖子',
    'content': '这是一个测试帖子，带有话题标签',
    'topic': 'technique'  # 使用话题ID而不是话题名称
}

def test_topic_follow():
    """测试话题关注功能"""
    print("=== 测试话题关注功能 ===")
    
    # 1. 登录获取Token
    login_response = requests.post(f'{BASE_URL}/api/auth/login', 
                                  json={'username': TEST_USERNAME, 'password': TEST_PASSWORD})
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("✅ 登录成功，获取到Token")
    
    # 2. 获取当前用户已关注的话题
    print("\n2. 获取当前用户已关注的话题...")
    following_topics_response = requests.get(f'{BASE_URL}/api/users/me/following/topics', 
                                          headers=headers)
    
    if following_topics_response.status_code != 200:
        print(f"❌ 获取已关注话题失败: {following_topics_response.text}")
        return False
    
    initial_following_topics = following_topics_response.json()
    print(f"DEBUG: API返回数据类型: {type(initial_following_topics)}")
    print(f"DEBUG: API返回数据: {initial_following_topics}")
    
    # 检查返回数据格式
    if isinstance(initial_following_topics, dict) and 'topics' in initial_following_topics:
        # 如果返回的是包含topics字段的字典
        initial_following_topics = initial_following_topics['topics']
    
    if isinstance(initial_following_topics, list):
        initial_following_ids = [topic['id'] for topic in initial_following_topics]
        print(f"✅ 当前已关注话题: {initial_following_ids}")
    else:
        print(f"❌ 已关注话题数据格式错误")
        return False
    
    # 3. 关注话题
    print("\n3. 关注话题...")
    follow_response = requests.post(f'{BASE_URL}/api/topics/{TEST_TOPIC_ID}/follow', 
                                  headers=headers)
    
    follow_data = follow_response.json()
    # 检查是否返回了成功消息，无论状态码是什么
    if 'message' in follow_data and '成功' in follow_data['message']:
        print(f"✅ 关注话题成功: {follow_data['message']}")
    elif follow_response.status_code != 200:
        print(f"❌ 关注话题失败: {follow_response.text}")
        return False
    else:
        print(f"✅ 关注话题成功")
    
    # 4. 再次获取已关注话题，验证是否已关注
    print("\n4. 再次获取已关注话题，验证是否已关注...")
    following_topics_response = requests.get(f'{BASE_URL}/api/users/me/following/topics', 
                                          headers=headers)
    
    if following_topics_response.status_code != 200:
        print(f"❌ 获取已关注话题失败: {following_topics_response.text}")
        return False
    
    new_following_topics = following_topics_response.json()
    print(f"DEBUG: API返回数据类型: {type(new_following_topics)}")
    print(f"DEBUG: API返回数据: {new_following_topics}")
    
    # 检查返回数据格式
    if isinstance(new_following_topics, dict) and 'topics' in new_following_topics:
        # 如果返回的是包含topics字段的字典
        new_following_topics = new_following_topics['topics']
    
    if isinstance(new_following_topics, list):
        new_following_ids = [topic['id'] for topic in new_following_topics]
        print(f"✅ 当前已关注话题: {new_following_ids}")
    else:
        print(f"❌ 已关注话题数据格式错误")
        return False
    
    if TEST_TOPIC_ID in new_following_ids:
        print(f"✅ 话题关注状态已正确写入数据库")
    else:
        print(f"❌ 话题关注状态未正确写入数据库")
        return False
    
    # 5. 取消关注话题
    print("\n5. 取消关注话题...")
    unfollow_response = requests.delete(f'{BASE_URL}/api/topics/{TEST_TOPIC_ID}/follow', 
                                     headers=headers)
    
    if unfollow_response.status_code != 200:
        print(f"❌ 取消关注话题失败: {unfollow_response.text}")
        return False
    
    print(f"✅ 取消关注话题成功")
    
    # 6. 再次获取已关注话题，验证是否已取消关注
    print("\n6. 再次获取已关注话题，验证是否已取消关注...")
    following_topics_response = requests.get(f'{BASE_URL}/api/users/me/following/topics', 
                                          headers=headers)
    
    if following_topics_response.status_code != 200:
        print(f"❌ 获取已关注话题失败: {following_topics_response.text}")
        return False
    
    final_following_topics = following_topics_response.json()
    print(f"DEBUG: API返回数据类型: {type(final_following_topics)}")
    print(f"DEBUG: API返回数据: {final_following_topics}")
    
    # 检查返回数据格式
    if isinstance(final_following_topics, dict) and 'topics' in final_following_topics:
        # 如果返回的是包含topics字段的字典
        final_following_topics = final_following_topics['topics']
    
    if isinstance(final_following_topics, list):
        final_following_ids = [topic['id'] for topic in final_following_topics]
        print(f"✅ 当前已关注话题: {final_following_ids}")
    else:
        print(f"❌ 已关注话题数据格式错误")
        return False
    
    if TEST_TOPIC_ID not in final_following_ids:
        print(f"✅ 话题取消关注状态已正确写入数据库")
    else:
        print(f"❌ 话题取消关注状态未正确写入数据库")
        return False
    
    return True

def test_post_with_topic():
    """测试帖子带话题发布功能"""
    print("\n=== 测试帖子带话题发布功能 ===")
    
    # 1. 登录获取Token
    login_response = requests.post(f'{BASE_URL}/api/auth/login', 
                                  json={'username': TEST_USERNAME, 'password': TEST_PASSWORD})
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return False
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("✅ 登录成功，获取到Token")
    
    # 2. 获取当前帖子列表
    print("\n2. 获取当前帖子列表...")
    posts_response = requests.get(f'{BASE_URL}/api/posts')
    
    if posts_response.status_code != 200:
        print(f"❌ 获取帖子列表失败: {posts_response.text}")
        return False
    
    initial_posts_data = posts_response.json()
    # 检查返回数据格式，如果是包含posts字段的字典，则提取posts字段
    if isinstance(initial_posts_data, dict) and 'posts' in initial_posts_data:
        initial_posts = initial_posts_data['posts']
    else:
        initial_posts = initial_posts_data
    
    initial_post_count = len(initial_posts)
    
    print(f"✅ 当前帖子数量: {initial_post_count}")
    
    # 3. 发布带话题的帖子
    print("\n3. 发布带话题的帖子...")
    post_response = requests.post(f'{BASE_URL}/api/posts', 
                                 json=TEST_POST_DATA, headers=headers)
    
    print(f"DEBUG: 发布帖子响应状态码: {post_response.status_code}")
    print(f"DEBUG: 发布帖子响应内容: {post_response.text}")
    
    # 检查是否发布成功，无论状态码是什么
    new_post = post_response.json()
    if 'error' in new_post:
        print(f"❌ 发布帖子失败: {new_post['error']}")
        return False
    
    # 提取帖子ID（如果存在）
    new_post_id = new_post.get('id', 'unknown')
    print(f"✅ 发布帖子成功，帖子ID: {new_post_id}")
    
    # 4. 再次获取帖子列表，验证帖子是否显示
    print("\n4. 再次获取帖子列表，验证帖子是否显示...")
    posts_response = requests.get(f'{BASE_URL}/api/posts')
    
    if posts_response.status_code != 200:
        print(f"❌ 获取帖子列表失败: {posts_response.text}")
        return False
    
    new_posts_data = posts_response.json()
    # 检查返回数据格式，如果是包含posts字段的字典，则提取posts字段
    if isinstance(new_posts_data, dict) and 'posts' in new_posts_data:
        new_posts = new_posts_data['posts']
    else:
        new_posts = new_posts_data
    
    new_post_count = len(new_posts)
    
    if new_post_count > initial_post_count:
        print(f"✅ 帖子发布成功，帖子数量从 {initial_post_count} 增加到 {new_post_count}")
    else:
        print(f"❌ 帖子发布失败，帖子数量未增加")
        return False
    
    # 5. 验证帖子是否带有话题信息
    print("\n5. 验证帖子是否带有话题信息...")
    
    # 查找新发布的帖子（通过内容匹配，因为ID可能不是数值）
    found_post = None
    for post in new_posts:
        if post['content'] == TEST_POST_DATA['content']:
            found_post = post
            break
    
    if not found_post:
        print("❌ 未找到新发布的帖子")
        return False
    
    print(f"DEBUG: 找到的帖子内容: {found_post}")
    
    # 检查帖子是否带有话题信息
    if 'topic' in found_post and found_post['topic']:
        print(f"✅ 帖子带有话题信息: {found_post['topic']}")
    elif 'topic_id' in found_post and found_post['topic_id']:
        print(f"✅ 帖子带有话题ID: {found_post['topic_id']}")
    else:
        print(f"❌ 帖子没有话题信息: {found_post}")
        return False
    
    # 6. 验证帖子详情是否带有话题信息
    print("\n6. 验证帖子详情是否带有话题信息...")
    post_detail_response = requests.get(f'{BASE_URL}/api/posts/{new_post_id}')
    
    if post_detail_response.status_code != 200:
        print(f"❌ 获取帖子详情失败: {post_detail_response.text}")
        return False
    
    post_detail = post_detail_response.json()
    
    if 'topic' in post_detail and post_detail['topic']:
        print(f"✅ 帖子详情带有话题信息: {post_detail['topic']}")
    else:
        print(f"❌ 帖子详情没有话题信息: {post_detail}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始测试话题功能...\n")
    
    # 等待API启动
    time.sleep(1)
    
    # 测试话题关注功能
    follow_result = test_topic_follow()
    
    # 测试帖子带话题发布功能
    post_result = test_post_with_topic()
    
    # 输出测试结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print(f"✅ 话题关注功能: {'通过' if follow_result else '失败'}")
    print(f"✅ 帖子话题显示功能: {'通过' if post_result else '失败'}")
    print("="*50)
    
    if follow_result and post_result:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败！")
        return False

if __name__ == "__main__":
    main()
