<script setup lang="ts">
    import { ref, computed, watch } from 'vue'
    import { marked } from 'marked'

    import { usePlayerStore } from '@/stores/PlayerStore'
    import { useSFX } from '@/composables/SFX'

    const props = defineProps<{
        sfx_id: string,
        traitSettingId?: string,
        adding?: boolean,
        editing?: boolean,
        expanded?: boolean
    }>()

    const emit = defineEmits([
        'expand',
        'collapse',
        'activate',
        'add',
        'remove'
    ])

    watch(() => props.expanded, (newVal) => {
        show_description.value = newVal
    })

    const player = usePlayerStore()
    const { sfx, retrieve_sfx, change_sfx } = useSFX(undefined, props.sfx_id)

    retrieve_sfx()

    const rendered_description = computed(() => 
        sfx.value.description ? marked.parse(sfx.value.description) : ''
    )

    function click_card() {
        console.log('click card')
        if(player.editing && !props.editing) return
        if(props.adding) show_description.value = !show_description.value
        if(show_description.value) {
			emit('collapse')
		} else {
            emit('expand')
        }
    }

    function activate() {
        // triggers the @activate event on Trait.vue
        // where the trait is added to the dice pool
        // with the selected sfx as metadata
        if(!props.adding) {
            emit('activate', sfx.value)
        }
    }

    function add() {
        // triggers the @add event on Trait.vue
        // where it is added to the trait setting
        show_description.value = false
        emit('add')
    }
    
    function remove() {
        // triggers the @remove event on Trait.vue
        // where it is removed from the trait setting
        show_description.value = false
        emit('remove')
    }

    const show_description = ref(props.expanded && !props.adding)
    const new_name = ref("")
    const new_description = ref("")
    const is_editing = ref(false)
    function toggle_edit() {
        is_editing.value = !is_editing.value
        if(is_editing.value) {
            new_name.value = sfx.value.name
            new_description.value = sfx.value.description
        }
    }
    function save_sfx() {
        change_sfx({ name: new_name.value, description: new_description.value })
        toggle_edit()
    }
</script>

<template>
    <div class="sfx" :class="[
                show_description ? 'expanded' : 'collapsed',
                props.adding ? 'adding' : 'playing',
                is_editing ? 'editing' : ''
            ]">
        <div class="viewing" v-if="!is_editing">
            <div class="sfx-title" :title="show_description ? 'collapse' : 'expand'" @click.stop="click_card">
                ✨ {{ sfx?.name }}
                <!-- <span class="tutorial" v-if="!player.small_buttons && show_description">← close ↓ activate</span> -->
            </div>
            <Transition name="desc">
                <div class="sfx-description" v-if="show_description && sfx?.description && !is_editing"
                    v-html="rendered_description" @click.stop="activate" title="play">
                </div>
            </Transition>
        </div>
        <div class="editing" v-else>
            ✨ <input class="edit-name" type="text" placeholder="name" v-model="new_name" />
            <textarea class="edit-description" placeholder="description" v-model="new_description" />
        </div>
        <div class="buttons">
            <input type="button" class="add button" value="add" @click.stop="add"
                v-if="show_description && props.adding" />
            <input type="button" class="save button" value="save" @click.stop="save_sfx"
                v-if="is_editing" />
            <input type="button" class="toggle-edit button" :value="is_editing ? 'cancel' : 'edit'" @click.stop="toggle_edit"
                v-if="player.is_gm && props.editing && show_description" />
            <input type="button" class="remove button" value="remove" @click.stop="remove"
                v-if="show_description && !props.adding && props.editing" />
        </div>
    </div>
</template>

<style scoped>
    .sfx {
        /* font-size: 1.2em; */
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
        .buttons {
            .add, .save {
                background-color: var(--color-highlight);
                color: var(--color-highlight-text);
            }
            .toggle-edit {
                background-color: var(--color-editing);
                color: var(--color-editing-text);
            }
			.remove {
				background-color: var(--color-hitch);
				color: var(--color-hitch-text);
			}
        }
        &.editing {
            /* background-color: var(--color-editing);
            color: var(--color-editing-text); */
            border: 1px solid var(--color-editing);
            border-radius: .4em;
            margin: .4em;
            .edit-name {
                font-size: 1.4em;
            }
            .edit-description {
                width: calc(100% - 2em);
                min-height: 4em;
                margin: .4em;
            }
            .buttons {
                display: flex;
                justify-content: center;
            }
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
            /* text-align: center; */
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
    .desc-enter-active,
    .desc-leave-active {
        transition: max-height .4s ease-out;
        max-height: 100px;
    }
    .desc-enter-from,
    .desc-leave-to {
        max-height: 0;
    }
}
</style>
