<script setup lang="ts">
	import { usePlayerStore } from '@/stores/PlayerStore';
	import { useEntity } from '@/composables/Entity';

	const player = usePlayerStore()
	const { entity, retrieve_entity } = useEntity(undefined, player.perspective_id)
	retrieve_entity()
</script>

<template>
	<div id="faction-wrapper">
		<h1>{{ entity.name }}</h1>
		
	</div>
</template>

<style scoped>
</style>
