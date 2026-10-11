from pathlib import Path

from fastapi.testclient import TestClient

from wepulse import api as api_module
from wepulse.db import Database
from wepulse.digest import render_digest
from wepulse.models import ArticleCandidate, utc_now
from wepulse.article_url import ArticleUrlError, parse_article_page
from wepulse.dashboard import ADMIN_HTML


def test_insert_is_idempotent(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    account_id = database.add_account("测试公众号", "manual", None, None)
    article = ArticleCandidate("article-1", "测试文章", "https://mp.weixin.qq.com/s/test", utc_now())
    assert database.insert_article(account_id, article) is True
    assert database.insert_article(account_id, article) is False
    assert len(database.recent_articles(24)) == 1


def test_digest_contains_account_and_link(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    account_id = database.add_account("测试公众号", "manual", None, None)
    database.insert_article(
        account_id,
        ArticleCandidate("article-1", "测试文章", "https://mp.weixin.qq.com/s/test", utc_now()),
    )
    digest = render_digest(database, 24)
    assert "测试公众号" in digest
    assert "[测试文章](https://mp.weixin.qq.com/s/test)" in digest


def test_digest_contains_collection_failure(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    account_id = database.add_account("异常来源", "rss", None, "https://example.com/feed.xml")
    database.set_account_state(account_id, "连接超时")
    digest = render_digest(database, 24)
    assert "需要处理的采集失败" in digest
    assert "异常来源" in digest
    assert "连接超时" in digest


def test_delete_account_cascades_articles(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    account_id = database.add_account("待删除来源", "manual", None, None)
    database.insert_article(
        account_id,
        ArticleCandidate("delete-me", "待删除文章", "https://example.com/delete", utc_now()),
    )
    assert database.delete_account(account_id) is True
    assert database.get_account(account_id) is None
    assert database.recent_articles(24) == []


def test_admin_dashboard_has_primary_actions():
    assert "WePulse 管理中心" in ADMIN_HTML
    assert "检查 Cookie" in ADMIN_HTML
    assert "测试每日推送" in ADMIN_HTML
    assert "不要把 Cookie 发给任何人" in ADMIN_HTML
    assert "录入或更新微信读书 Cookie" in ADMIN_HTML
    assert "/api/config/weread-cookie" in ADMIN_HTML


def test_admin_http_and_authenticated_status(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(api_module.database, "path", tmp_path / "api.db")
    monkeypatch.setattr(api_module.settings, "admin_token", "unit-test-token")
    with TestClient(api_module.app) as client:
        page = client.get("/admin")
        assert page.status_code == 200
        assert "WePulse 管理中心" in page.text
        assert client.get("/api/status").status_code == 401
        status = client.get(
            "/api/status", headers={"Authorization": "Bearer unit-test-token"}
        )
        assert status.status_code == 200
        assert status.json()["schedule"]["timezone"] == "Asia/Shanghai"


def test_cookie_can_be_saved_without_echoing_secret(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("ADMIN_TOKEN=unit-test-token\nWEREAD_COOKIE=\n", encoding="utf-8")
    monkeypatch.setattr(api_module, "ENV_PATH", env_path)
    monkeypatch.setattr(api_module.settings, "admin_token", "unit-test-token")
    monkeypatch.setattr(api_module.settings, "weread_cookie", "")
    monkeypatch.setattr(api_module.service.collectors["weread"], "cookie", "")
    cookie = "wr_vid=123456; wr_skey=secret-value; wr_rt=another-value"
    with TestClient(api_module.app) as client:
        response = client.put(
            "/api/config/weread-cookie",
            headers={"Authorization": "Bearer unit-test-token"},
            json={"cookie": cookie},
        )
    assert response.status_code == 200
    assert cookie not in response.text
    assert f"WEREAD_COOKIE={cookie}" in env_path.read_text(encoding="utf-8")
    assert api_module.settings.weread_cookie == cookie
    assert api_module.service.collectors["weread"].cookie == cookie


def test_cookie_rejects_control_characters(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(api_module, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr(api_module.settings, "admin_token", "unit-test-token")
    with TestClient(api_module.app) as client:
        response = client.put(
            "/api/config/weread-cookie",
            headers={"Authorization": "Bearer unit-test-token"},
            json={"cookie": "wr_vid=123; wr_skey=bad\u0016value"},
        )
    assert response.status_code == 422
    assert not (tmp_path / ".env").exists()


def test_windows_local_entrypoints_are_shipped():
    root = Path(__file__).resolve().parents[1]
    expected = [
        "start-wepulse.cmd",
        "start-local.ps1",
        "stop-wepulse.cmd",
        "stop-local.ps1",
        "restart-wepulse.cmd",
        "open-config.cmd",
        "install-autostart.cmd",
        "install-autostart.ps1",
        "remove-autostart.cmd",
        "remove-autostart.ps1",
    ]
    assert all((root / name).is_file() for name in expected)
    assert "start-local.ps1" in (root / "start-wepulse.cmd").read_text(encoding="utf-8")


def test_parse_public_article_metadata():
    page = '''
    <meta property="og:title" content="示例标题" />
    <script>
    var nickname = htmlDecode("示例公众号");
    window.logs = {biz: "MTIzNDU2", mid: "9001", idx: "1"};
    var ct = "1791275274";
    </script>
    '''
    result = parse_article_page("https://mp.weixin.qq.com/s/example", page)
    assert result.account_name == "示例公众号"
    assert result.source_id == "MP_WXS_123456"
    assert result.article.title == "示例标题"
    assert result.article.external_id == "wx:MTIzNDU2:9001:1"


def test_reject_non_wechat_url():
    try:
        parse_article_page("https://example.com/article", "")
    except ArticleUrlError:
        pass
    else:
        raise AssertionError("non-WeChat URL should be rejected")
