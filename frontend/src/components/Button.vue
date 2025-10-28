<template>
    <button
        :class="['btn', `btn-${props.variant}`]"
        :type="props.type"
        @click="onClick"
        v-bind="$attrs"
    >
        <slot>{{ props.label }}</slot>
    </button>
</template>

<script setup>
const props = defineProps({
    label: { type: String, default: 'Button' },
    variant: { 
        type: String, 
        default: 'primary', validator: (value) => [
            'primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark', 'link'
        ].includes(value) 
    },
    type: { type: String, default: 'button' }
})

const emit = defineEmits(['click'])

function onClick(e) {
    emit('click', e)
}
</script>
