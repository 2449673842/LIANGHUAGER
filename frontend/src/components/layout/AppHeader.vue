<template>
  <header class="header">
    <div class="header__left">
      <div class="header__search">
        <span>⌕</span>
        <input placeholder="搜索策略、标的、任务或运行会话" />
      </div>
    </div>
    <div class="header__right">
      <span class="mini-badge">OKX / 现货 + 永续</span>
      <span class="mini-badge">提醒: 邮件 + 企微</span>
      <div class="header__user">
        <div class="header__avatar">SZ</div>
        <div>
          <strong>Administrator</strong>
          <p>多账户交易工作区</p>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 78px;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(217, 229, 239, 0.95);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
}

.header__left,
.header__right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header__search {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 420px;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid #d9e5ef;
  background: white;
}

.header__search input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
}

.header__user {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 6px;
}

.header__avatar {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  background: #ffde3d;
  color: #5d4a00;
  font-weight: 800;
}

.header__user strong,
.header__user p {
  display: block;
  margin: 0;
}

.header__user p {
  font-size: 12px;
  color: #6f879f;
}
</style>
