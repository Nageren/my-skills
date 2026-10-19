// 云效 Thoughts Slate 编辑器 DOM -> Markdown 转换器（v2 完整版）
// 用法：注入到已打开的文档页，返回 JSON.stringify({ok, title, md})
// 已实测：36 篇文档（含表格 25 篇、代码块 9 篇、图片 8 篇）
(function () {
  function getText(el) {
    var parts = [];
    function walk(node) {
      if (node.nodeType === 3) {
        parts.push(node.nodeValue || '');
        return;
      }
      if (node.nodeType !== 1) return;
      var tag = node.tagName;
      if (['BUTTON', 'SVG', 'PATH'].indexOf(tag) > -1) return;
      if (tag === 'BR') { parts.push('\n'); return; }
      var cls = node.className ? node.className.toString() : '';
      // 跳过工具栏 UI 元素
      if (cls.indexOf('trigger-box') > -1 || cls.indexOf('btn-box') > -1 ||
          cls.indexOf('tool-more') > -1 || cls.indexOf('copy') > -1 ||
          cls.indexOf('hover-area') > -1) return;
      for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i]);
    }
    walk(el);
    return parts.join('');
  }

  function cleanText(s) {
    return s.replace(/\u200b/g, '').replace(/\s+/g, ' ').trim();
  }

  // 图片 URL 可能被前端截断（中间 ...），截断时改用无签名 thumbnail 源
  function getImageUrl(block) {
    var img = block.querySelector('img');
    if (img && img.src) {
      if (img.src.indexOf('...') === -1) return img.src;
      var m = /storage\/([0-9a-f]+)/.exec(img.src);
      if (m) return 'https://tcs-devops.aliyuncs.com/thumbnail/' + m[1] + '/w/2000/h/2000';
    }
    var bg = block.querySelector('[style*="background-image"]');
    if (bg) {
      var mm = /url\(['"]?(.*?)['"]?\)/.exec(bg.style.backgroundImage || '');
      if (mm) {
        if (mm[1].indexOf('...') === -1) return mm[1];
        var m2 = /storage\/([0-9a-f]+)/.exec(mm[1]);
        if (m2) return 'https://tcs-devops.aliyuncs.com/thumbnail/' + m2[1] + '/w/2000/h/2000';
      }
    }
    return '';
  }

  function convertBlock(el) {
    var type = el.getAttribute('data-type');
    var out = '';
    switch (type) {
      case 'title': out = '# ' + cleanText(getText(el)) + '\n'; break;
      case 'header-one': out = '## ' + cleanText(getText(el)) + '\n'; break;
      case 'header-two': out = '### ' + cleanText(getText(el)) + '\n'; break;
      case 'header-three': out = '#### ' + cleanText(getText(el)) + '\n'; break;
      case 'header-four': out = '##### ' + cleanText(getText(el)) + '\n'; break;
      case 'paragraph': {
        var t = cleanText(getText(el));
        if (t) out = t + '\n';
        break;
      }
      case 'image': {
        var src = getImageUrl(el);
        if (src) out = '![image](' + src + ')\n';
        break;
      }
      default: break;
    }
    return out;
  }

  function convertTable(el) {
    var out = [];
    var rows = el.querySelectorAll('tr');
    var matrix = [];
    for (var i = 0; i < rows.length; i++) {
      var cells = [];
      var tds = rows[i].querySelectorAll('th, td');
      var allEmpty = true;
      for (var j = 0; j < tds.length; j++) {
        var c = cleanText(getText(tds[j]));
        cells.push(c);
        if (c) allEmpty = false;
      }
      // 过滤全空行（空 thead 会污染表头）
      if (!allEmpty) matrix.push(cells);
    }
    if (matrix.length === 0) return '';
    var header = matrix[0];
    out.push('| ' + header.join(' | ') + ' |');
    out.push('|' + header.map(function () { return ' --- '; }).join('|') + '|');
    for (var r = 1; r < matrix.length; r++) {
      out.push('| ' + matrix[r].join(' | ') + ' |');
    }
    return out.join('\n') + '\n';
  }

  function convert() {
    var root = document.querySelector('div[data-slate-editor=true]');
    if (!root) return JSON.stringify({ err: 'NO_EDITOR', title: document.title });
    var md = '';
    function process(el) {
      var type = el.getAttribute && el.getAttribute('data-type');
      var tag = el.tagName;
      // 表格整体处理
      if (tag === 'TABLE') { md += convertTable(el); return; }
      // 代码块：pre 直接取文本（data-type=code 会误伤 SVG 图标，勿用）
      if (tag === 'PRE') {
        var code = el.innerText || '';
        md += '```\n' + code.replace(/\n+$/, '') + '\n```\n';
        return;
      }
      if (type && ['title', 'header-one', 'header-two', 'header-three', 'header-four', 'paragraph', 'image'].indexOf(type) > -1) {
        md += convertBlock(el);
        return;
      }
      for (var i = 0; i < el.children.length; i++) process(el.children[i]);
    }
    for (var i = 0; i < root.children.length; i++) process(root.children[i]);
    md = md.replace(/\n{3,}/g, '\n\n').trim() + '\n';
    return JSON.stringify({ ok: true, title: document.title, md: md });
  }

  return convert();
})()
