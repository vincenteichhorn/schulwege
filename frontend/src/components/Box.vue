<script setup>
const props = defineProps({
    grow: {
        type: Boolean,
        default: false
    },
    direction: {
        type: String,
        default: 'vertical',
        validator: (value) => ['vertical', 'horizontal'].includes(value)
    },
    align: {
        type: String,
        default: 'center',
        validator: (value) => ['start', 'center', 'end', 'stretch'].includes(value)
    }
})
</script>

<template>
    <div
        class="box"
        :class="[
            {
                'box--grow': props.grow,
                'box--horizontal': props.direction === 'horizontal',
                'box--vertical': props.direction === 'vertical'
            },
            `box--align-${props.align}`
        ]"
    >
        <slot />
    </div>
</template>

<style scoped>
.box {
    padding: 16px;
    border: 1px solid #f7f7f7;
    border-radius: 8px;
    background: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    width: max-content;
}
.box--grow {
    width: 100%;
}
.box--horizontal {
    display: flex;
    flex-direction: row;
    gap: 12px;
}
.box--vertical {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

/* alignment (uses align-items to align along cross axis) */
.box--align-start {
    align-items: flex-start;
}
.box--align-center {
    align-items: center;
}
.box--align-end {
    align-items: flex-end;
}
.box--align-stretch {
    align-items: stretch;
}
</style>