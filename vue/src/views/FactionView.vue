<script setup lang="ts">
	import { usePlayer } from '@/stores/Player';
	import { useEntity } from '@/composables/Entity';

	const player = usePlayer()
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
