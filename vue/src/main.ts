import './assets/main.css'

import { createApp, provide, h } from 'vue'

import { createPinia } from 'pinia'
import piniaPluginPersistedState from 'pinia-plugin-persistedstate'

import { ApolloClient, createHttpLink, InMemoryCache } from '@apollo/client/core'

import App from './App.vue'
import router from './router'

const ip_address = import.meta.env.VITE_PUBLIC_IP ?? 'localhost'

// HTTP connection to the API
const httpLink = createHttpLink({
	uri: 'http://' + ip_address + ':5000/graphql'
})

// Cache implementation
const cache = new InMemoryCache({ addTypename: false })

// Create the apollo client
const apolloClient = new ApolloClient({
	link: httpLink,
	cache,
	// connectToDevTools: true, // disable for production !!
})

setInterval(() => {
	console.log('GC')
	apolloClient.cache.gc()
	// apolloClient.cache.reset()
}, 30000)

import { DefaultApolloClient } from '@vue/apollo-composable'

const app = createApp({
	setup () {
		provide(DefaultApolloClient, apolloClient)
	},
  
	render: () => h(App),
})

app.provide('apolloClient', apolloClient)
app.provide('API_URL', 'http://' + ip_address + ':5000/')
app.provide('DIE_RATINGS', ['d4', 'd6', 'd8', 'd10', 'd12'])
app.provide('MEDIA_FOLDER', '/assets/uploads/')
const pinia = createPinia()
pinia.use(piniaPluginPersistedState)
app.use(pinia)
app.use(router)

import Vue3TouchEvents, {
	type Vue3TouchEventsOptions,
} from "vue3-touch-events";

app.use<Vue3TouchEventsOptions>(Vue3TouchEvents, {
	disableClick: false
})

import VueSortable from 'vue3-sortablejs'
import process from 'process'

app.use(VueSortable)

app.mount('#app')
