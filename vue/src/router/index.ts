import { createRouter, createWebHistory } from 'vue-router'
import RulesView from '@/views/RulesView.vue'
import SettingsView from '@/views/SettingsView.vue'
import CharacterView from '@/views/CharacterView.vue'
import CharacterOverview from '@/views/CharacterOverview.vue'
import CurrentLocationView from '@/views/CurrentLocationView.vue'
import TraitsetOverview from '@/views/TraitsetOverview.vue'
import TraitsetView from '@/views/TraitsetView.vue'
import SFXOverview from '@/views/SFXOverview.vue'
import CodexView from '@/views/CodexView.vue'

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [

		{
			path: '/',
			name: 'Landing',
			component: SettingsView
		},
		{
			path: '/entity/:entity_key',
			name: 'Entity',
			component: CharacterView
		},
		{
			path: '/rules',
			name: 'Rules',
			component: RulesView
		},
		{
			path: '/settings',
			name: 'SettingsView',
			component: SettingsView
		},
		{
			path: '/characters',
			name: 'Character overview',
			component: CharacterOverview
		},
		{
			path: '/character/:id',
			name: 'Characters',
			component: CharacterView
		},
		{
			path: '/traitsets',
			name: 'Traitset overview',
			component: TraitsetOverview
		},
		{
			path: '/traitsets/:id',
			name: 'Traitsets',
			component: TraitsetView
		},
		{
			path: '/sfxs',
			name: 'SFX overview',
			component: SFXOverview
		},
		{
			path: '/location/:location_key',
			name: 'Location',
			component: CurrentLocationView,
			props: true,
			children: [
				{
					path: 'entity/:entity_key',
					name: 'Entity',
					component: CharacterView
				},
				{
					path: 'settings',
					name: 'Settings',
					children: [
						{
							path: 'characters',
							name: 'Characters',
							component: CharacterOverview
						},
						{
							path: 'traitsets',
							name: 'Traitsets',
							component: TraitsetOverview
						},
						{
							path: 'traitset/:traitset_key',
							name: 'Traitset',
							component: TraitsetView
						},
						{
							path: 'sfxs',
							name: 'SFXs',
							component: SFXOverview
						},
						{
							path: 'rules',
							name: 'Rules',
							component: RulesView
						}
					]
				},
				{
					path: 'contacts',
					name: 'Contacts',
					component: CodexView
				}
			]
		},
	]
})

export default router
