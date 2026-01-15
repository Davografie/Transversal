<script setup lang="ts">
	import { watch, ref } from 'vue'
	import { marked } from 'marked'
	import { useSFX } from '@/composables/SFX';

	const props = defineProps<{
		sfx_id: string
	}>()

	const { sfx, retrieve_sfx, retrieve_traits, change_sfx, delete_sfx } = useSFX(undefined, props.sfx_id)
	retrieve_sfx()
	retrieve_traits()
	watch(sfx, (newSfx, oldSfx) => {
		if(newSfx && newSfx.id != oldSfx?.id) {
			retrieve_traits()
		}
	})

	const new_name = ref(sfx.value.name)
	const new_description = ref(sfx.value.description)

	const editing_sfx = ref(false)

	function toggle_editing() {
		new_name.value = sfx.value.name
		new_description.value = sfx.value.description
		editing_sfx.value = !editing_sfx.value
	}

	function save_sfx() {
		change_sfx({ name: new_name.value, description: new_description.value })
		setTimeout(() => retrieve_sfx(), 200)
	}
</script>

<template>
	<div class="sfx-edit-wrapper" @click="toggle_editing">
		<div class="sfx-details" v-if="!editing_sfx">
			<div class="sfx-name">{{ sfx.name }}</div>
			<div class="sfx-description" v-html="marked.parse(sfx.description)"></div>
			<div class="sfx-traits">
				<span class="button" v-for="trait in sfx.traits">
					{{ trait.name }}
				</span>
			</div>
		</div>
		<div class="sfx-edit" v-else>
			<div><input class="sfx-name" type="text" v-model="new_name" /></div>
			<div><textarea class="sfx-description" v-model="new_description" /></div>
		</div>
		<div v-if="editing_sfx">
			<input type="button" class="button" value="update" @click.stop="save_sfx" />
			<input type="button" class="button" value="delete" @click.stop="delete_sfx()" />
			<input type="button" class="button" value="cancel" @click.stop="editing_sfx = false" />
		</div>
	</div>
</template>

<style scoped>
	.sfx-edit-wrapper {
		.sfx-name {
			font-size: 1.2em;
		}
		.sfx-edit {
			.sfx-description {
				width: 100%;
				min-height: 100px;
			}
		}
	}
</style>
