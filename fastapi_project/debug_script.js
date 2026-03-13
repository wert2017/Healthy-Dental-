const { createApp, ref, computed, onMounted } = Vue

        createApp({
            setup() {
                const searchQuery = ref('')
                const pacientes = ref([])
                const dashboardData = ref([])
                const groupedAtenciones = ref({})
                const loading = ref(false)
                let timeout = null

                // Tratamiento Modal State
                const showTratamientoModal = ref(false)
                const selectedPaciente = ref(null)
                const activeTreatments = ref([])
                const allTreatments = ref([])
                const selectedNewTreatment = ref(null)
                const isReportModalOpen = ref(false)

                // --- AUTH SETUP ---
                const token = localStorage.getItem('token')
                if (!token) {
                    window.location.href = '/login'
                }
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

                axios.interceptors.response.use(
                    response => response,
                    error => {
                        if (error.response && (error.response.status === 401 || error.response.status === 403)) {
                            localStorage.removeItem('token')
                            window.location.href = '/login'
                        }
                        return Promise.reject(error)
                    }
                )

                const logout = () => {
                    localStorage.removeItem('token')
                    window.location.href = '/login'
                }
                // --- END AUTH ---

                const loadDashboard = async () => {
                    try {
                        const res = await axios.get('/api/atenciones/dashboard')
                        dashboardData.value = res.data

                        // Group by date
                        const groups = {}
                        res.data.forEach(item => {
                            if (!groups[item.fecha_dia]) {
                                groups[item.fecha_dia] = []
                            }
                            groups[item.fecha_dia].push(item)
                        })
                        groupedAtenciones.value = groups
                    } catch (error) {
                        console.error(error)
                    }
                }

                const conciliar = async (item) => {
                    if (item.validado) return
                    if (!confirm(`¿Conciliar atención de ${item.paciente.nombres}? Una vez validado no se podrá editar.`)) return

                    try {
                        await axios.post(`/api/atenciones/${item.id}/validar`)
                        loadDashboard()
                    } catch (error) {
                        alert('Error al validar')
                    }
                }

                onMounted(() => {
                    loadDashboard()
                })

                const searchPacientes = async () => {
                    if (searchQuery.value.length < 2) {
                        pacientes.value = []
                        return
                    }
                    loading.value = true
                    try {
                        const res = await axios.get(`/api/pacientes?q=${searchQuery.value}`)
                        pacientes.value = res.data
                    } catch (error) {
                        console.error(error)
                    } finally {
                        loading.value = false
                    }
                }

                const debounceSearch = () => {
                    clearTimeout(timeout)
                    timeout = setTimeout(searchPacientes, 300)
                }

                const crearAtencion = async (pacienteId) => {
                    try {
                        const res = await axios.post(`/api/atenciones?paciente_id=${pacienteId}`)
                        window.location.href = `/recepcion/editar/${res.data.id}`
                    } catch (error) {
                        alert('Error al crear atención')
                        console.error(error)
                    }
                }

                // --- TRATAMIENTO MODAL LOGIC ---
                const openTratamientoModal = async (paciente) => {
                    selectedPaciente.value = paciente
                    showTratamientoModal.value = true
                    selectedNewTreatment.value = null

                    try {
                        const [activeRes, allRes] = await Promise.all([
                            axios.get(`/api/pacientes/${paciente.id}/tratamientos-activos`),
                            axios.get('/api/tratamientos')
                        ])
                        activeTreatments.value = activeRes.data
                        allTreatments.value = allRes.data
                    } catch (error) {
                        console.error(error)
                        alert('Error cargando tratamientos')
                    }
                }

                const closeTratamientoModal = () => {
                    showTratamientoModal.value = false
                    selectedPaciente.value = null
                }

                const startTreatment = async () => {
                    if (!selectedNewTreatment.value) return
                    try {
                        await axios.post(`/api/pacientes/${selectedPaciente.value.id}/tratamientos?tratamiento_id=${selectedNewTreatment.value}`)
                        const res = await axios.get(`/api/pacientes/${selectedPaciente.value.id}/tratamientos-activos`)
                        activeTreatments.value = res.data
                        selectedNewTreatment.value = null
                    } catch (error) {
                        alert(error.response?.data?.detail || 'Error iniciando tratamiento')
                    }
                }

                const finishTreatment = async (t) => {
                    if (!confirm(`¿Finalizar el tratamiento de ${t.nombre}?`)) return
                    try {
                        await axios.put(`/api/pacientes/${selectedPaciente.value.id}/tratamientos/${t.tratamiento_id}/finalizar`)
                        const res = await axios.get(`/api/pacientes/${selectedPaciente.value.id}/tratamientos-activos`)
                        activeTreatments.value = res.data
                    } catch (error) {
                        alert('Error finalizando tratamiento')
                    }
                }

                const deleteAtencion = async (id) => {
                    if (!confirm('¿Estás seguro de eliminar esta atención?')) return
                    try {
                        await axios.delete(`/api/atenciones/${id}`)
                        await loadDashboard()
                    } catch (error) {
                        alert('Error eliminando atención: ' + (error.response?.data?.detail || error.message))
                    }
                }

                const dailyReport = computed(() => {
                    let ef = 0, tr = 0, tc = 0, extra = 0

                    if (dashboardData.value) {
                        dashboardData.value.forEach(item => {
                            if (item.pagos) {
                                item.pagos.forEach(p => {
                                    if (p.forma_pago === 'EF') ef += parseFloat(p.monto || 0)
                                    if (p.forma_pago === 'TR') tr += parseFloat(p.monto || 0)
                                    if (p.forma_pago === 'TC') tc += parseFloat(p.monto || 0)
                                })
                            }
                            const paid = (item.pagos || []).reduce((sum, p) => sum + parseFloat(p.monto || 0), 0)
                            const cost = parseFloat(item.total || 0)
                            if (paid > cost) {
                                extra += (paid - cost)
                            }
                        })
                    }

                    return {
                        efectivo: ef,
                        transferencia: tr,
                        tarjeta: tc,
                        total: ef + tr + tc,
                        extra: extra
                    }
                })

                return {
                    token, logout,
                    groupedAtenciones,
                    searchQuery, pacientes, searchPacientes, debounceSearch,
                    crearAtencion,
                    showTratamientoModal, selectedPaciente, activeTreatments, allTreatments, selectedNewTreatment,
                    openTratamientoModal, closeTratamientoModal, startTreatment, finishTreatment,
                    deleteAtencion, conciliar,
                    // Renamed Modal State
                    isReportModalOpen,
                    dailyReport
                }
            }
        }).mount('#app')
