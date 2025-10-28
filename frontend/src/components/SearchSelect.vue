<template>
    <div class="search-select">
        <div class="input-row">
            <input
                type="text"
                :placeholder="placeholder"
                v-model="inputValue"
                @keydown.down.prevent="focusNext()"
                @keydown.up.prevent="focusPrev()"
                @keydown.enter.prevent="acceptFocused()"
                @blur="onBlur"
                @focus="open = true"
                @click="open = true"
                class="search-input"
            />
            <span class="status">
                <span v-if="isSelectedOrSingle" class="check">✓</span>
                <span v-else-if="loading" class="loading">...</span>
                <span v-else-if="noMatches" class="cross">✕</span>
            </span>
        </div>

        <ul v-if="open && matchedOptions.length" class="options-list" ref="list">
            <li
                v-for="(opt, idx) in matchedOptions.slice(0, props.displayAllLimit)"
                :key="opt + '-' + idx"
                :class="['option-item', { focused: idx === focusedIndex }]"
                @mousedown.prevent="selectOption(opt)"
                @mouseenter="focusedIndex = idx"
            >
                {{ opt }}
            </li>
        </ul>
    </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

/*
Props:
- options: Array<string> | Function (can return Array<string> or Promise<Array<string>>)
- placeholder: input placeholder
- debounce: ms debounce for calling function options
- index: default focused index
Emits:
- select (when an item is selected / auto-selected)
*/

const props = defineProps({
    options: {
        type: [Array, Function],
        required: true
    },
    placeholder: {
        type: String,
        default: 'Search...'
    },
    debounce: {
        type: Number,
        default: 200
    },
    displayAllLimit: {
        type: Number,
        default: 5
    },
    index: {
        type: Number,
        default: -1
    }
})

const emit = defineEmits(['update:modelValue', 'select'])

const inputValue = ref(props.index >= 0 && Array.isArray(props.options) ? props.options[props.index] || '' : '')
const matchedOptions = ref([])
const loading = ref(false)
const open = ref(false)
const selected = ref(props.index >= 0 ? props.options[props.index] || null : null)
const focusedIndex = ref(props.index)

let callId = 0
let debounceTimeout = null

watch(inputValue, (val, old) => {
    // Clear selection if user edits away
    if (selected.value !== val) {
        selected.value = null
        emitSelection(null)
    }

    scheduleFetch(val)
})

function scheduleFetch(val) {
    if (debounceTimeout) clearTimeout(debounceTimeout)
    debounceTimeout = setTimeout(() => {
        fetchOptions(val)
    }, props.debounce)
}

async function fetchOptions(q) {
    loading.value = true
    const myCall = ++callId
    try {
        let res = []
        if (typeof props.options === 'function') {
            // allow sync or async
            res = await props.options(q)
        } else if (Array.isArray(props.options) && props.options.length >= props.displayAllLimit) {
            // filter by case-insensitive substring match
            const qLower = (q || '').toLowerCase()
            if (qLower === '') {
                res = props.options.slice()
            } else {
                res = props.options.filter((s) =>
                    String(s).toLowerCase().includes(qLower)
                )
            }
        } else if (Array.isArray(props.options) && props.options.length < props.displayAllLimit) {
            res = props.options
        }

        // Only accept latest call
        if (myCall === callId) {

            matchedOptions.value = Array.isArray(res) ? res.map(String) : []
            focusedIndex.value = matchedOptions.value.length ? 0 : -1

            // If exactly one result, auto-select it (emit)
            if (matchedOptions.value.length === 1) {
                const one = matchedOptions.value[0]
                // if input equals that option already, mark selected; otherwise select & emit
                if (inputValue.value !== one) {
                    inputValue.value = one
                    // selected will be updated via watcher on inputValue, but set here explicitly
                    selected.value = one
                } else {
                    selected.value = one
                }
                emitSelection(one)
            }
        }
    } catch (e) {
        // ignore errors from user-supplied function
        matchedOptions.value = []
    } finally {
        if (myCall === callId) loading.value = false
    }
}

function selectOption(opt) {
    inputValue.value = opt
    selected.value = opt
    emitSelection(opt)
    // keep the list open briefly so click is obvious, then close
    open.value = false
}

function emitSelection(val) {
    emit('select', val)
}

const noMatches = computed(() => !loading.value && open.value && matchedOptions.value.length === 0)
const isSelectedOrSingle = computed(() => {
    // show check when we have a selected value matching input or when matched options length is 1
    return (selected.value && selected.value === inputValue.value) || (matchedOptions.value.length === 1)
})

function focusNext() {
    if (!matchedOptions.value.length) return
    focusedIndex.value = Math.min(matchedOptions.value.length - 1, focusedIndex.value + 1)
    scrollFocusedIntoView()
}

function focusPrev() {
    if (!matchedOptions.value.length) return
    focusedIndex.value = Math.max(0, focusedIndex.value - 1)
    scrollFocusedIntoView()
}

function acceptFocused() {
    if (focusedIndex.value >= 0 && matchedOptions.value[focusedIndex.value]) {
        selectOption(matchedOptions.value[focusedIndex.value])
    }
}

const list = ref(null)
function scrollFocusedIntoView() {
    // simple scroll into view if the element exists
    if (!list.value) return
    const el = list.value.children[focusedIndex.value]
    if (el && typeof el.scrollIntoView === 'function') el.scrollIntoView({ block: 'nearest' })
}

function onBlur() {
    // close list shortly after blur (allow click selection to proceed)
    setTimeout(() => {
        open.value = false
    }, 150)
}

// initial fetch
fetchOptions(inputValue.value)
if (props.index >= 0 && Array.isArray(props.options)) {
    const initial = props.options[props.index] || null
    if (initial) {
        inputValue.value = initial
        selected.value = initial
        emitSelection(initial)
    }
}
</script>

<style scoped>
.search-select {
    width: 100%;
    max-width: 250px;
    position: relative;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

.input-row {
    position: relative;
    display: flex;
    align-items: center;
}

.search-input {
    width: 100%;
    padding: 8px 10px;
    box-sizing: border-box;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    outline: none;
}

.search-input:focus {
    border-color: #3182ce;
    box-shadow: 0 0 0 3px rgba(49,130,206,0.12);
}

.status {
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none; /* clicking won't close input */
    font-size: 16px;
    line-height: 1;
    width: auto;
}

.check {
    color: #16a34a;
}

.cross {
    color: #dc2626;
}

.options-list {
    margin: 6px 0 0 0;
    padding: 0;
    list-style: none;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    max-height: 220px;
    overflow: auto;
    background: white;
    position: absolute;
    width: 100%;
    z-index: 50;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}

.option-item {
    padding: 8px 10px;
    cursor: pointer;
}

.option-item:hover,
.option-item.focused {
    background: #e6f2ff;
}

.loading,
.no-results {
    margin-top: 6px;
    font-size: 13px;
    color: #6b7280;
}
</style>