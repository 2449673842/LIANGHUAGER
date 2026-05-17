<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="$emit('cancel')">
        <div class="modal-card" :style="cardStyle">
          <div class="modal-card__head">
            <h3>{{ title }}</h3>
            <p v-if="subtitle">{{ subtitle }}</p>
          </div>
          <div class="modal-card__body">
            <slot>
              <div v-for="field in fields" :key="field.key" class="modal-field">
                <template v-if="field.type === 'select'">
                  <label>{{ field.label }}</label>
                  <select v-model="values[field.key]">
                    <option v-for="opt in field.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </template>
                <template v-else-if="field.suggestions">
                  <label>{{ field.label }}</label>
                  <div class="search-wrap">
                    <input v-model="values[field.key]" :placeholder="field.placeholder || ''"
                      @input="onSearchInput(field.key, field.suggestions)"
                      @focus="onSearchFocus(field.key, field.suggestions)"
                      @blur="onSearchBlur"
                      @keydown.down.prevent="searchNav(field.key, 1)"
                      @keydown.up.prevent="searchNav(field.key, -1)"
                      @keydown.enter.prevent="searchSelect(field.key)" />
                    <ul v-if="searchState.visible" class="search-dropdown">
                      <li v-for="(item,i) in searchState.filtered" :key="item" :class="{ active: i === searchState.hoverIndex }"
                        @mousedown.prevent="searchPick(field.key, item)" @mouseenter="searchState.hoverIndex = i">
                        <span class="search-icon">◯</span> {{ item }}
                      </li>
                      <li v-if="searchState.filtered.length === 0" class="search-empty">无匹配结果</li>
                    </ul>
                  </div>
                </template>
                <template v-else>
                  <label>{{ field.label }}</label>
                  <input v-model="values[field.key]" :placeholder="field.placeholder || ''" :type="field.type || 'text'" @keyup.enter="emitConfirm" />
                </template>
                <div v-if="field.hint" class="field-hint">{{ field.hint }}</div>
              </div>
            </slot>
          </div>
          <div class="modal-card__actions">
            <button v-if="!hideCancel" class="button" @click="$emit('cancel')">取消</button>
            <button v-if="!hideConfirm" class="button button--primary" @click="emitConfirm">{{ confirmText || '确认' }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, watch, computed } from 'vue'

export interface ModalField {
  key: string
  label: string
  placeholder?: string
  type?: string
  suggestions?: string[]
  options?: Array<{ value: string; label: string }>
  hint?: string
}

const props = withDefaults(defineProps<{
  visible: boolean
  title: string
  subtitle?: string
  fields?: ModalField[]
  confirmText?: string
  hideCancel?: boolean
  hideConfirm?: boolean
  width?: string
}>(), { fields: () => [], hideCancel: false, hideConfirm: false })

const emit = defineEmits<{ confirm: [values: Record<string, string>]; cancel: [] }>()

const cardStyle = computed(() => props.width ? { width: props.width } : {})
const values = reactive<Record<string, string>>({})

const searchState = reactive({
  visible: false,
  filtered: [] as string[],
  hoverIndex: 0,
  sourceKey: '',
})

function onSearchInput(key: string, items: string[]) {
  const q = (values[key] || '').toLowerCase()
  searchState.filtered = items.filter(i => i.toLowerCase().includes(q))
  searchState.hoverIndex = 0
  searchState.visible = searchState.filtered.length > 0
  searchState.sourceKey = key
}

function onSearchFocus(key: string, items: string[]) {
  if (!values[key]) {
    searchState.filtered = items.slice()
    searchState.hoverIndex = 0
    searchState.visible = true
    searchState.sourceKey = key
  }
}

function onSearchBlur() { setTimeout(() => { searchState.visible = false }, 160) }
function searchNav(key: string, dir: number) {
  const n = searchState.filtered.length
  if (n === 0) return
  searchState.hoverIndex = (searchState.hoverIndex + dir + n) % n
}
function searchSelect(key: string) {
  const idx = searchState.hoverIndex
  if (idx >= 0 && idx < searchState.filtered.length) {
    values[key] = searchState.filtered[idx]
    searchState.visible = false
  }
}
function searchPick(key: string, item: string) {
  values[key] = item
  searchState.visible = false
}

watch(() => props.visible, (vis) => {
  if (vis && props.fields) {
    props.fields.forEach(f => { values[f.key] = '' })
    searchState.visible = false
  }
}, { immediate: true })

watch(() => props.fields, (flds) => {
  if (flds) flds.forEach(f => { if (!(f.key in values)) values[f.key] = '' })
}, { immediate: true })

function emitConfirm() { emit('confirm', { ...values }) }
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; background: rgba(15, 30, 55, 0.32); backdrop-filter: blur(6px); }
.modal-card { display: grid; gap: 20px; width: 400px; max-width: 94vw; padding: 24px 28px 20px; background: rgba(255, 255, 255, 0.97); border: 1px solid rgba(204, 219, 229, 0.9); border-radius: 18px; box-shadow: 0 24px 64px rgba(100, 125, 155, 0.18), 0 4px 12px rgba(0, 0, 0, 0.06); }
.modal-card__head h3 { margin: 0; font-size: 20px; color: #10213a; }
.modal-card__head p { margin: 6px 0 0; font-size: 13px; color: #7790a6; }
.modal-card__body { display: grid; gap: 14px; }
.modal-card__actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 4px; }
.modal-field { display: grid; gap: 6px; }
.modal-field label { font-size: 13px; font-weight: 600; color: #4c6782; }
.modal-field select, .modal-field input { min-height: 42px; padding: 0 14px; border: 1px solid #d9e5ef; border-radius: 12px; background: #f8fbfd; color: #132238; font-size: 14px; outline: none; transition: border-color 0.15s; }
.modal-field select:focus, .modal-field input:focus { border-color: #2eb8f6; background: #fff; box-shadow: 0 0 0 3px rgba(46, 184, 246, 0.08); }
.modal-card__actions .button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #d9e5ef; background: #fff; border-radius: 12px; min-height: 40px; padding: 0 18px; color: #26415f; font-size: 14px; cursor: pointer; transition: background .15s; }
.modal-card__actions .button:hover { background: #f4f8fb; }
.modal-card__actions .button--primary { background: linear-gradient(135deg, #16c8d0 0%, #2fb7f6 100%); color: #fff; border: none; box-shadow: 0 8px 20px rgba(43, 179, 226, 0.18); }
.modal-card__actions .button--primary:hover { box-shadow: 0 12px 28px rgba(43, 179, 226, 0.28); }
.field-hint { margin-top: 2px; font-size: 12px; color: #9bb1c4; line-height: 1.4; }
.search-wrap { position: relative; }
.search-dropdown { position: absolute; top: 100%; left: 0; right: 0; z-index: 10; margin: 4px 0 0; padding: 6px; list-style: none; background: #fff; border: 1px solid #d9e5ef; border-radius: 12px; box-shadow: 0 12px 40px rgba(100,125,155,0.16); max-height: 210px; overflow-y: auto; }
.search-dropdown li { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; color: #26415f; font-size: 14px; cursor: pointer; transition: background .1s; }
.search-dropdown li:hover, .search-dropdown li.active { background: #ecf5fc; }
.search-dropdown .search-empty { color: #7790a6; cursor: default; justify-content: center; }
.search-icon { color: #9bb1c4; font-size: 13px; }
.modal-enter-active, .modal-leave-active { transition: opacity .22s ease; }
.modal-enter-active .modal-card, .modal-leave-active .modal-card { transition: transform .22s ease, opacity .22s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-card { transform: scale(.94) translateY(12px); opacity: 0; }
.modal-leave-to .modal-card { transform: scale(.96) translateY(6px); opacity: 0; }
</style>
