<template>
    <header class="navbar" role="navigation" aria-label="Main navigation">
        <div class="nav-inner">
            <a class="brand" :href="brandHref">
                <slot name="brand">
                    <span class="brand-logo">{{ title }}</span>
                </slot>
            </a>

            <nav class="links" :class="{ open: mobileOpen }" aria-label="Primary">
                <RouterLink
                    v-for="(link, i) in links"
                    :key="i"
                    :to="link.href || '#'"
                    class="nav-link"
                    @click="closeMobile"
                >
                    {{ link.name }}
                </RouterLink>
            </nav>

            <div class="actions">
                <button
                    class="hamburger"
                    @click="toggleMobile"
                    :aria-expanded="mobileOpen.toString()"
                    aria-label="Toggle menu"
                >
                    <span class="bar" :class="{ active: mobileOpen }"></span>
                    <span class="bar" :class="{ active: mobileOpen }"></span>
                    <span class="bar" :class="{ active: mobileOpen }"></span>
                </button>
            </div>
        </div>
    </header>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
    title: { type: String, default: 'Schulkinder' },
    brandHref: { type: String, default: '/' },
    links: {type: Array}
})

const mobileOpen = ref(false)

function toggleMobile() {
    mobileOpen.value = !mobileOpen.value
}

function closeMobile() {
    mobileOpen.value = false
}
</script>

<style scoped>
.navbar {
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    height: 64px;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(6px);
    box-shadow: 0 1px 6px rgba(16,24,40,0.08);
    z-index: 1000;
    margin-bottom: 24px;
}

.nav-inner {
    max-width: 1100px;
    margin: 0 auto;
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
}

/* Brand */
.brand {
    display: flex;
    align-items: center;
    text-decoration: none;
    color: #0f172a;
    font-weight: 600;
    font-size: 1.05rem;
    margin-right: auto;
}
.brand-logo {
    display: inline-block;
    font-size: 2em;
}

/* Links */
.links {
    display: flex;
    gap: 12px;
    align-items: center;
}
.nav-link {
    color: #0f172a;
    text-decoration: none;
    padding: 8px 10px;
    border-radius: 6px;
    transition: background .15s, color .15s;
}
.nav-link:hover {
    background: rgba(15,23,42,0.06);
}

/* Actions */
.actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Button */
.btn {
    background: #0ea5a6;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
}
.btn:hover { opacity: .95 }

/* Hamburger (mobile) */
.hamburger {
    display: none;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: transparent;
    border: none;
    padding: 6px;
    cursor: pointer;
    align-items: center;
    justify-content: center;
}
.bar {
    display: block;
    height: 2px;
    background: #0f172a;
    margin: 4px 0;
    transition: transform .2s ease, opacity .2s ease;
}
.bar.active:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.bar.active:nth-child(2) { opacity: 0; }
.bar.active:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

/* Responsive */
@media (max-width: 768px) {
    .links {
        position: absolute;
        top: 64px;
        left: 0;
        right: 0;
        background: rgba(255,255,255,0.98);
        flex-direction: column;
        gap: 0;
        overflow: hidden;
        max-height: 0;
        transition: max-height 220ms ease;
        box-shadow: 0 4px 20px rgba(2,6,23,0.08);
    }
    .links.open { max-height: 320px; }
    .nav-link {
        padding: 12px 16px;
        border-bottom: 1px solid rgba(15,23,42,0.04);
    }

    .hamburger { display: flex; }
    .actions .btn { display: none; }
}
</style>