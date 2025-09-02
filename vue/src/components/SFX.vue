<script setup lang="ts">
    import { ref, computed } from 'vue'
    import { marked } from 'marked'

    import { usePlayer } from '@/stores/Player'
    import { useSFX } from '@/composables/SFX'

    const props = defineProps<{
        sfx_id: string,
        traitSettingId?: string,
        adding?: boolean
        editing?: boolean
    }>()

    const emit = defineEmits([
        'expand',
        'collapse',
        'activate',
        'add',
        'remove'
    ])

    const player = usePlayer()
    const { sfx } = useSFX(undefined, props.sfx_id)
    const rendered_description = computed(() => 
        sfx.value.description ? marked.parse(sfx.value.description) : ''
    )
    function click_card(event: MouseEvent) {
        console.log('click card')
        if(player.editing && !props.editing) return
        event.stopPropagation()
        show_description.value = !show_description.value
        if(show_description.value) {
            emit('expand')
        } else {
            emit('collapse')
        }
    }
    function activate() {
        emit('activate', sfx.value)
    }
    function add() {
        show_description.value = false
        emit('add')
    }
    function remove() {
        show_description.value = false
        emit('remove')
    }
    const show_description = ref(false)
</script>

<template>
    <div class="sfx" :class="[
                show_description ? 'expanded' : 'collapsed',
                props.adding ? 'adding' : 'playing',
            ]"
            @click.stop="(e) => props.adding ? click_card(e) : null">
        <div class="sfx-title"
                @click="click_card" :title="show_description ? 'collapse' : 'expand'">
            {{ sfx?.name }}
            <span class="tutorial" v-if="!player.small_buttons && show_description">← close ↓ activate</span>
        </div>
        <div class="sfx-description" v-if="show_description && sfx?.description"
            v-html="rendered_description" @click.stop="props.adding ? click_card($event) : activate" title="play">
        </div>
        <input type="button" class="button" value="add" @click.stop="add" 
            v-if="show_description && props.adding" />
        <input type="button" class="button" value="remove" @click.stop="remove" 
            v-if="show_description && !props.adding && props.editing" />
    </div>
</template>

<style scoped>
    .sfx {
        font-size: 1.2em;
        .sfx-title {
            white-space: nowrap;
            cursor: pointer;
        }
        .sfx-description >>> ul {
            list-style-type: none;
            list-style-position: inside;
            padding: 0 .4em .4em .4em;
        }
        .sfx-description >>> ul li {
            margin: 0 .4em .4em .4em;
            padding: 0 .4em;
        }
        .sfx-description >>> ul li ul {
            padding: .4em .4em 0 .4em;
        }
        .tutorial {
            font-size: .8em;
        }
    }
    .sfx.collapsed {
        padding: .4em .8em;
    }
    .sfx.expanded {
        padding: .6em .4em;
        flex-grow: 1;
        .sfx-title {
            font-weight: bold;
            text-align: center;
        }
    }
    .sfx.adding {
        display: flex;
        flex-direction: column;
        .sfx-title {
            text-align: left;
        }
    }
    .sfx.adding.collapsed {
        background-color: var(--color-background);
        border: 1px solid var(--color-border);
        padding: .2em .4em;
    }
    .sfx.adding.expanded {
        width: 100%;
        border-top: 1px solid var(--color-border);
        border-bottom: 1px solid var(--color-border);
        margin: 0 .4em;
        cursor: pointer;
    }
</style>

<style>
.dark {
    .sfx.adding.collapsed {
        border-radius: 20px;
        padding: .2em 1em;
    }
}
</style>
