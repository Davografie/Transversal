<script setup lang="ts">
	import { marked } from 'marked'
	import { ref, type Ref } from 'vue'
	import { useSFXList } from '@/composables/SFXList'
	const { sfx_list, retrieve_sfx_list, create_sfx, update_sfx, delete_sfx } = useSFXList()
	const new_sfx_name: Ref<string> = ref('')
	const new_sfx_description: Ref<string> = ref('')
	function new_sfx() {
		create_sfx(new_sfx_name.value, new_sfx_description.value)
		retrieve_sfx_list()
	}
	function change_sfx() {
		update_sfx(editing_sfx.value, new_name.value, new_description.value)
		editing_sfx.value = ''
		setTimeout(retrieve_sfx_list, 200)
	}
	function remove_sfx(id:string) {
		delete_sfx(id)
		setTimeout(retrieve_sfx_list, 200)
	}
	const editing_sfx: Ref<string> = ref('')
	const new_name: Ref<string> = ref('')
	const new_description: Ref<string> = ref('')
	function focus_sfx(id: string) {
		if(editing_sfx.value != id) {
			editing_sfx.value = id
			new_name.value = sfx_list.value.find(sfx => sfx.id == id)?.name ?? ''
			new_description.value = sfx_list.value.find(sfx => sfx.id == id)?.description ?? ''
		}
	}
</script>

<template>
	<div id="sfx-overview-wrapper">
		<input type="button" class="button" value="refresh" @click="retrieve_sfx_list" />
		<div id="new-sfx">
			<div>
				<input type="text" placeholder="name" v-model="new_sfx_name" />
			</div>
			<div>
				<textarea class="description" placeholder="description" v-model="new_sfx_description" />
			</div>
			<input type="button" class="button" value="create"
				@click="new_sfx" />
		</div>
		<div id="sfx-list">
			<div class="sfx" :class="editing_sfx == sfx.id ? 'editing' : ''" v-for="sfx in sfx_list" @click="focus_sfx(sfx.id)">
				<div v-if="editing_sfx != sfx.id">
					<div class="sfx-name">{{ sfx.name }}</div>
					<div class="sfx-description" v-html="marked.parse(sfx.description)"></div>
				</div>
				<div v-else>
					<div><input class="name" type="text" v-model="new_name" /></div>
					<div><textarea class="description" v-model="new_description" /></div>
				</div>
				<div v-if="editing_sfx == sfx.id">
					<input type="button" class="button" value="update" @click.stop="change_sfx()" />
					<input type="button" class="button" value="delete" @click.stop="remove_sfx(sfx.id)" />
					<input type="button" class="button" value="cancel" @click.stop="editing_sfx = ''" />
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
	#sfx-list {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		padding-bottom: 100px;
		.sfx {
			/* display: inline-block; */
			vertical-align: top;
			white-space: wrap;
			flex-grow: 1;
			/* max-width: 30%; */
			padding: 0 .5rem;
			margin: .5rem;
			border: 1px solid var(--color-border);
			background-color: var(--color-background-mute);
			.sfx-name {
				font-weight: bold;
			}
		}
		.sfx.editing {
			/* display: block; */
			border-top: 1px solid var(--color-highlight);
			border-bottom: 1px solid var(--color-highlight);
			width: 100%;
			max-width: 100%;
			.name {
				width: 100%;
				text-align: center;
				font-size: 1.2em;
				margin: .5em 0;
				padding: .5em 0;
			}
			.description {
				width: 100%;
				height: 100px;
			}
		}
	}
</style>

<style>
.landscape {
	#sfx-overview-wrapper {
		padding-top: 4em;
	}
}
</style>
