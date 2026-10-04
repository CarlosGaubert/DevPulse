/**
 * DevPulse - Editorial Reader & Radar Engine
 * Equipped with full UI & Article Translation System (ES / EN)
 */

const App = () => {
    return {
        // Data State
        articles: [],
        leadArticle: null,
        regularArticles: [],
        topics: [],
        stats: {
            total_articles: 0,
            avg_importance_score: 0,
            total_sources: 0,
            verified_safe_count: 0,
            blocked_threats_count: 0,
            last_collected_at: null
        },
        scheduler: {
            is_active: true,
            is_syncing: false,
            sync_interval_minutes: 15,
            next_run_at: null,
            last_run_at: null
        },

        // View & Reader State
        selectedTopic: '',
        sortBy: 'importance',
        searchQuery: '',
        minScore: '',
        page: 1,
        pageSize: 15,
        totalPages: 1,
        totalArticles: 0,
        isLoading: false,
        isSyncing: false,
        viewMode: localStorage.getItem('devpulse_view') || 'magazine',
        savedArticleIds: JSON.parse(localStorage.getItem('devpulse_saved') || '[]'),
        showSavedOnly: false,
        readingArticle: null,

        // Translation Engine State
        currentLang: localStorage.getItem('devpulse_lang') || 'es', // 'es' | 'en'
        translatingId: null,

        // Theme: Grayscale Dark / Clean Light
        darkMode: localStorage.getItem('devpulse_theme') === 'dark' || 
                 (!localStorage.getItem('devpulse_theme') && window.matchMedia('(prefers-color-scheme: dark)').matches),

        // Available Languages
        availableLanguages: [
            { code: 'es', name: 'Español', flag: '🇪🇸' },
            { code: 'en', name: 'English', flag: '🇬🇧' },
            { code: 'pt', name: 'Português', flag: '🇵🇹' },
            { code: 'fr', name: 'Français', flag: '🇫🇷' },
            { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
        ],
        langDropdownOpen: false,

        // Feed Manager State
        showFeedModal: false,
        systemFeeds: [],
        customFeeds: [],
        newFeedName: '',
        newFeedUrl: '',
        newFeedTopic: 'Herramientas de Desarrollo & CLI',
        isAddingFeed: false,
        feedMessage: '',
        feedMessageType: '',

        // Export State
        showExportModal: false,

        searchDebounceTimer: null,
        autoPollTimer: null,


        // Localization Dictionary
        i18n: {
            es: {
                edition: 'Edición Continua en Tiempo Real',
                shield_active: 'Escudo Antimalware Activo',
                radar_active: 'Radar Autónomo',
                next_scan: 'Próximo escaneo',
                news_verified: 'noticias verificadas',
                subtitle: 'Información actual de tecnologías emergentes, diálogo explicativo y lectura en 15 segundos.',
                search_placeholder: 'Buscar novedades técnicas...',
                bookmarks: 'Guardados',
                sync: 'Sincronizar',
                syncing: 'Escaneando...',
                all_topics: 'Todos los Tópicos',
                showing: 'Mostrando',
                of: 'de',
                news: 'noticias',
                reset_filters: 'Restablecer filtros',
                all_impact: 'Todo el espectro de impacto',
                high_impact: '🔥 Alto Impacto (≥ 75)',
                moderate_impact: '⚡ Relevancia Moderada (≥ 50)',
                sort_impact: 'Impacto & Frescura Reciente',
                sort_recent: 'Más Recientes',
                featured_cover: 'Novedad Destacada • Portada',
                dialogue_title: 'Diálogo Explicativo • ¿Por qué importa a los desarrolladores?',
                highlights_title: 'Ideas Principales • Lectura en 15 Segundos',
                reading_time: 'seg de lectura',
                focus_reader: 'Lector Concentrado',
                original_source: 'Fuente Original Segura',
                read_in_15s: 'Leer en 15s',
                save: 'Guardar',
                saved: 'Guardado',
                prev_page: '← Página Anterior',
                next_page: 'Página Siguiente →',
                page: 'Página',
                close: 'Cerrar',
                inspect_security: 'Inspección de Seguridad & Antimalware Web',
                score_label: 'Puntuación',
                safe_link: 'Enlace Seguro & Protegido',
                verified: 'Verificado',
                translate_btn: 'Traducir / Original',
                translating: 'Traduciendo...',
                lang_switch_label: 'Idioma: Español (ES)',
                empty_title: 'No se encontraron noticias en esta sección',
                empty_desc: 'El radar autónomo continúa monitoreando fuentes. Prueba con otro tópico o realiza una búsqueda manual.',
                scan_now: 'Escanear Fuentes Ahora',
                footer_credit: 'Radar Tecnológico Automatizado con Traducción & Escudo Antimalware',
                feed_manager: 'Fuentes & RSS',
                export_digest: 'Exportar Briefing',
                export_md: 'Exportar Markdown (.md)',
                export_json: 'Exportar JSON (.json)',
                system_sources: 'Fuentes del Sistema',
                custom_sources: 'Fuentes Personalizadas',
                add_new_feed: 'Añadir Nueva Fuente RSS/Atom',
                feed_name: 'Nombre de la Fuente',
                feed_url: 'URL del Feed RSS',
                feed_topic: 'Tópico Asignado',
                btn_add_feed: 'Validar y Agregar',
                no_custom_feeds: 'No has agregado fuentes personalizadas aún.',
                delete_feed: 'Eliminar',
                active: 'Activo',
                paused: 'Pausado',
                saved_empty_export: 'No tienes noticias guardadas aún para exportar.'
            },
            en: {
                edition: 'Continuous Real-Time Edition',
                shield_active: 'Active Antimalware Shield',
                radar_active: 'Autonomous Radar',
                next_scan: 'Next scan',
                news_verified: 'verified stories',
                subtitle: 'Real-time breakthroughs in emerging tech, explanatory dialogue and 15-second executive summaries.',
                search_placeholder: 'Search technical breakthroughs...',
                bookmarks: 'Saved',
                sync: 'Sync',
                syncing: 'Scanning...',
                all_topics: 'All Topics',
                showing: 'Showing',
                of: 'of',
                news: 'stories',
                reset_filters: 'Reset filters',
                all_impact: 'All impact levels',
                high_impact: '🔥 High Impact (≥ 75)',
                moderate_impact: '⚡ Moderate Relevance (≥ 50)',
                sort_impact: 'Impact & Freshness',
                sort_recent: 'Most Recent',
                featured_cover: 'Featured Story • Front Page',
                dialogue_title: 'Explanatory Dialogue • Why developers should care',
                highlights_title: 'Key Highlights • 15-Second Read',
                reading_time: 'sec read',
                focus_reader: 'Focus Reader',
                original_source: 'Original Verified Source',
                read_in_15s: 'Read in 15s',
                save: 'Save',
                saved: 'Saved',
                prev_page: '← Previous Page',
                next_page: 'Next Page →',
                page: 'Page',
                close: 'Close',
                inspect_security: 'Web Security & Antimalware Audit',
                score_label: 'Score',
                safe_link: 'Safe & Verified Link',
                verified: 'Verified',
                translate_btn: 'Translate / Original',
                translating: 'Translating...',
                lang_switch_label: 'Language: English (EN)',
                empty_title: 'No stories found in this section',
                empty_desc: 'The autonomous radar is continuously scanning. Try another topic or search query.',
                scan_now: 'Scan Sources Now',
                footer_credit: 'Automated Tech Radar with Universal Translation & Antimalware Shield',
                feed_manager: 'Sources & RSS',
                export_digest: 'Export Briefing',
                export_md: 'Export Markdown (.md)',
                export_json: 'Export JSON (.json)',
                system_sources: 'System Sources',
                custom_sources: 'Custom Sources',
                add_new_feed: 'Add New RSS/Atom Feed',
                feed_name: 'Source Name',
                feed_url: 'RSS Feed URL',
                feed_topic: 'Assigned Category',
                btn_add_feed: 'Validate & Add',
                no_custom_feeds: 'No custom feeds added yet.',
                delete_feed: 'Delete',
                active: 'Active',
                paused: 'Paused',
                saved_empty_export: 'No saved stories to export yet.'
            },
            pt: {
                edition: 'Edição Contínua em Tempo Real',
                shield_active: 'Escudo Antimalware Ativo',
                radar_active: 'Radar Autônomo',
                next_scan: 'Próxima verificação',
                news_verified: 'notícias verificadas',
                subtitle: 'Avanços em tecnologia de ponta, diálogo explicativo e leitura executiva em 15 segundos.',
                search_placeholder: 'Pesquisar inovações técnicas...',
                bookmarks: 'Salvos',
                sync: 'Sincronizar',
                syncing: 'Escaneando...',
                all_topics: 'Todos os Tópicos',
                showing: 'Mostrando',
                of: 'de',
                news: 'notícias',
                reset_filters: 'Redefinir filtros',
                all_impact: 'Todo o espectro de impacto',
                high_impact: '🔥 Alto Impacto (≥ 75)',
                moderate_impact: '⚡ Relevância Moderada (≥ 50)',
                sort_impact: 'Impacto & Atualidade',
                sort_recent: 'Mais Recentes',
                featured_cover: 'Destaque Principal • Capa',
                dialogue_title: 'Diálogo Explicativo • Por que isso importa para desenvolvedores?',
                highlights_title: 'Pontos Principais • Leitura em 15 Segundos',
                reading_time: 'seg de leitura',
                focus_reader: 'Leitor Concentrado',
                original_source: 'Fonte Original Segura',
                read_in_15s: 'Ler em 15s',
                save: 'Salvar',
                saved: 'Salvo',
                prev_page: '← Página Anterior',
                next_page: 'Próxima Página →',
                page: 'Página',
                close: 'Fechar',
                inspect_security: 'Auditoria de Segurança Web & Antimalware',
                score_label: 'Pontuação',
                safe_link: 'Link Seguro e Verificado',
                verified: 'Verificado',
                translate_btn: 'Traduzir / Original',
                translating: 'Traduzindo...',
                lang_switch_label: 'Idioma: Português (PT)',
                empty_title: 'Nenhuma notícia encontrada nesta seção',
                empty_desc: 'O radar autônomo continua buscando novidades. Tente outro tópico ou busca.',
                scan_now: 'Verificar Fontes Agora',
                footer_credit: 'Radar Tecnológico Automatizado com Tradução & Proteção Antimalware',
                feed_manager: 'Fontes & RSS',
                export_digest: 'Exportar Resumo',
                export_md: 'Exportar Markdown (.md)',
                export_json: 'Exportar JSON (.json)',
                system_sources: 'Fontes do Sistema',
                custom_sources: 'Fontes Personalizadas',
                add_new_feed: 'Adicionar Feed RSS/Atom',
                feed_name: 'Nome da Fonte',
                feed_url: 'URL do Feed RSS',
                feed_topic: 'Categoria',
                btn_add_feed: 'Validar e Adicionar',
                no_custom_feeds: 'Nenhuma fonte personalizada adicionada ainda.',
                delete_feed: 'Excluir',
                active: 'Ativo',
                paused: 'Pausado',
                saved_empty_export: 'Nenhuma notícia salva para exportar.'
            },
            fr: {
                edition: 'Édition Continue en Temps Réel',
                shield_active: 'Bouclier Antimalware Actif',
                radar_active: 'Radar Autonome',
                next_scan: 'Prochain scan',
                news_verified: 'articles vérifiés',
                subtitle: 'Actualités technologiques émergentes, dialogue explicatif et résumés en 15 secondes.',
                search_placeholder: 'Rechercher des nouveautés...',
                bookmarks: 'Sauvegardés',
                sync: 'Synchroniser',
                syncing: 'Analyse en cours...',
                all_topics: 'Tous les Sujets',
                showing: 'Affichage',
                of: 'sur',
                news: 'articles',
                reset_filters: 'Réinitialiser les filtres',
                all_impact: 'Tous les niveaux d\'impact',
                high_impact: '🔥 Fort Impact (≥ 75)',
                moderate_impact: '⚡ Pertinence Modérée (≥ 50)',
                sort_impact: 'Impact & Fraîcheur',
                sort_recent: 'Plus Récents',
                featured_cover: 'À la Une • Couverture',
                dialogue_title: 'Dialogue Explicatif • Pourquoi cela compte pour les développeurs ?',
                highlights_title: 'Points Clés • Lecture en 15 Secondes',
                reading_time: 'sec de lecture',
                focus_reader: 'Lecteur Concentré',
                original_source: 'Source Originale Sécurisée',
                read_in_15s: 'Lire en 15s',
                save: 'Sauvegarder',
                saved: 'Sauvegardé',
                prev_page: '← Page Précédente',
                next_page: 'Page Suivante →',
                page: 'Page',
                close: 'Fermer',
                inspect_security: 'Audit Sécurité Web & Antimalware',
                score_label: 'Score',
                safe_link: 'Lien Sécurisé & Vérifié',
                verified: 'Vérifié',
                translate_btn: 'Traduire / Original',
                translating: 'Traduction...',
                lang_switch_label: 'Langue: Français (FR)',
                empty_title: 'Aucun article trouvé dans cette section',
                empty_desc: 'Le radar autonome continue de surveiller les flux. Essayez un autre sujet ou recherche.',
                scan_now: 'Scanner les Sources',
                footer_credit: 'Radar Technologique Automatisé avec Traduction & Bouclier de Sécurité',
                feed_manager: 'Sources & RSS',
                export_digest: 'Exporter le Briefing',
                export_md: 'Exporter Markdown (.md)',
                export_json: 'Exporter JSON (.json)',
                system_sources: 'Sources Système',
                custom_sources: 'Sources Personnalisées',
                add_new_feed: 'Ajouter un Flux RSS/Atom',
                feed_name: 'Nom de la Source',
                feed_url: 'URL du Flux RSS',
                feed_topic: 'Catégorie',
                btn_add_feed: 'Valider et Ajouter',
                no_custom_feeds: 'Aucun flux personnalisé pour le moment.',
                delete_feed: 'Supprimer',
                active: 'Actif',
                paused: 'En pause',
                saved_empty_export: 'Aucun article sauvegardé à exporter.'
            },
            de: {
                edition: 'Kontinuierliche Echtzeit-Ausgabe',
                shield_active: 'Aktiver Antimalware-Schutz',
                radar_active: 'Autonomes Radar',
                next_scan: 'Nächster Scan',
                news_verified: 'geprüfte Meldungen',
                subtitle: 'Aktuelle technologische Durchbrüche, erklärender Dialog und 15-Sekunden-Kurzfassungen.',
                search_placeholder: 'Technische Updates suchen...',
                bookmarks: 'Gespeichert',
                sync: 'Sync',
                syncing: 'Scannen...',
                all_topics: 'Alle Themen',
                showing: 'Zeige',
                of: 'von',
                news: 'Meldungen',
                reset_filters: 'Filter zurücksetzen',
                all_impact: 'Alle Relevanzstufen',
                high_impact: '🔥 Hohe Relevanz (≥ 75)',
                moderate_impact: '⚡ Moderate Relevanz (≥ 50)',
                sort_impact: 'Relevanz & Aktualität',
                sort_recent: 'Neueste zuerst',
                featured_cover: 'Top-Thema • Titelseite',
                dialogue_title: 'Erklärender Dialog • Warum dies für Entwickler wichtig ist',
                highlights_title: 'Hauptpunkte • In 15 Sekunden gelesen',
                reading_time: 'Sek. Lesezeit',
                focus_reader: 'Fokus-Lesemodus',
                original_source: 'Geprüfte Originalquelle',
                read_in_15s: 'In 15s lesen',
                save: 'Speichern',
                saved: 'Gespeichert',
                prev_page: '← Vorherige Seite',
                next_page: 'Nächste Seite →',
                page: 'Seite',
                close: 'Schließen',
                inspect_security: 'Websicherheit & Antimalware-Prüfung',
                score_label: 'Punktzahl',
                safe_link: 'Sicherer & Geprüfter Link',
                verified: 'Verifiziert',
                translate_btn: 'Übersetzen / Original',
                translating: 'Übersetze...',
                lang_switch_label: 'Sprache: Deutsch (DE)',
                empty_title: 'Keine Meldungen in diesem Bereich gefunden',
                empty_desc: 'Das autonome Radar scannt kontinuierlich weiter. Versuchen Sie eine andere Kategorie oder Suche.',
                scan_now: 'Quellen jetzt scannen',
                footer_credit: 'Automatisiertes Tech-Radar mit Übersetzung & Malware-Schutzschild',
                feed_manager: 'Quellen & RSS',
                export_digest: 'Briefing exportieren',
                export_md: 'Markdown exportieren (.md)',
                export_json: 'JSON exportieren (.json)',
                system_sources: 'System-Quellen',
                custom_sources: 'Benutzerdefinierte Feeds',
                add_new_feed: 'Neuen RSS/Atom-Feed hinzufügen',
                feed_name: 'Name der Quelle',
                feed_url: 'RSS-Feed-URL',
                feed_topic: 'Kategorie',
                btn_add_feed: 'Prüfen & Hinzufügen',
                no_custom_feeds: 'Noch keine benutzerdefinierten Feeds hinzugefügt.',
                delete_feed: 'Löschen',
                active: 'Aktiv',
                paused: 'Pausiert',
                saved_empty_export: 'Noch keine gespeicherten Meldungen zum Exportieren vorhanden.'
            }
        },


        // Helper translation getter
        t(key) {
            const langDict = this.i18n[this.currentLang] || this.i18n.es;
            return langDict[key] || key;
        },

        // Toggle global language (ES <-> EN)
        toggleLanguage() {
            this.currentLang = (this.currentLang === 'es') ? 'en' : 'es';
            localStorage.setItem('devpulse_lang', this.currentLang);
            this.loadNews(false);
        },

        setLanguage(code) {
            this.currentLang = code;
            localStorage.setItem('devpulse_lang', code);
            this.langDropdownOpen = false;
            this.loadNews(false);
        },

        getCurrentLangObj() {
            return this.availableLanguages.find(l => l.code === this.currentLang) || this.availableLanguages[0];
        },

        // Current Date formatted for the masthead
        get formattedDate() {
            const locale = (this.currentLang === 'es') ? 'es-ES' : 'en-US';
            return new Intl.DateTimeFormat(locale, { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            }).format(new Date());
        },

        // Initialize application
        async init() {
            this.applyTheme();
            
            window.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.readingArticle) {
                    this.closeReader();
                }
            });

            await Promise.all([
                this.loadTopics(),
                this.loadStats(),
                this.loadNews()
            ]);

            this.autoPollTimer = setInterval(() => {
                this.checkSchedulerStatus();
            }, 12000);
        },

        toggleTheme() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('devpulse_theme', this.darkMode ? 'dark' : 'light');
            this.applyTheme();
        },

        applyTheme() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },

        setViewMode(mode) {
            this.viewMode = mode;
            localStorage.setItem('devpulse_view', mode);
        },

        // Load news with current language
        async loadNews(resetPage = false) {
            if (resetPage) this.page = 1;
            this.isLoading = true;

            const params = new URLSearchParams({
                page: this.page,
                page_size: this.pageSize,
                sort_by: this.sortBy,
                lang: this.currentLang
            });

            if (this.selectedTopic) params.append('topic', this.selectedTopic);
            if (this.searchQuery.trim()) params.append('search', this.searchQuery.trim());
            if (this.minScore) params.append('min_score', this.minScore);

            try {
                const res = await fetch(`/api/news?${params.toString()}`);
                if (!res.ok) throw new Error('Error al cargar noticias');
                const data = await res.json();
                
                let items = data.items;

                if (this.showSavedOnly) {
                    items = items.filter(a => this.savedArticleIds.includes(a.id));
                }

                this.articles = items;
                this.totalArticles = data.total;
                this.totalPages = data.total_pages;
                this.page = data.page;

                if (this.page === 1 && !this.searchQuery && !this.selectedTopic && items.length > 0) {
                    this.leadArticle = items[0];
                    this.regularArticles = items.slice(1);
                } else {
                    this.leadArticle = null;
                    this.regularArticles = items;
                }

            } catch (err) {
                console.error('Error fetching news:', err);
            } finally {
                this.isLoading = false;
            }
        },

        async loadTopics() {
            try {
                const res = await fetch('/api/topics');
                if (res.ok) {
                    const data = await res.json();
                    this.topics = data.topics;
                }
            } catch (err) {
                console.error('Error fetching topics:', err);
            }
        },

        async loadStats() {
            try {
                const res = await fetch('/api/stats');
                if (res.ok) {
                    const data = await res.json();
                    this.stats = {
                        total_articles: data.total_articles,
                        avg_importance_score: data.avg_importance_score,
                        total_sources: data.total_sources,
                        verified_safe_count: data.verified_safe_count || data.total_articles,
                        blocked_threats_count: data.blocked_threats_count || 0,
                        last_collected_at: data.last_collected_at
                    };
                    if (data.scheduler) {
                        this.scheduler = data.scheduler;
                    }
                }
            } catch (err) {
                console.error('Error fetching stats:', err);
            }
        },

        getSafetyBadge(status, score) {
            if (status === 'VERIFIED_SAFE') {
                return {
                    label: this.t('safe_link'),
                    shortLabel: this.t('verified'),
                    classes: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20',
                    dotClass: 'bg-emerald-500',
                    isSafe: true
                };
            } else if (status === 'WARNING') {
                return {
                    label: 'Advertencia de Enlace',
                    shortLabel: 'Precaución',
                    classes: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20',
                    dotClass: 'bg-amber-500',
                    isSafe: false
                };
            } else {
                return {
                    label: 'Amenaza Bloqueada',
                    shortLabel: 'Bloqueado',
                    classes: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20',
                    dotClass: 'bg-rose-500',
                    isSafe: false
                };
            }
        },

        async checkSchedulerStatus() {
            try {
                const res = await fetch('/api/scheduler/status');
                if (res.ok) {
                    const prevSyncing = this.scheduler.is_syncing;
                    this.scheduler = await res.json();
                    
                    if (prevSyncing && !this.scheduler.is_syncing) {
                        await Promise.all([
                            this.loadNews(),
                            this.loadTopics(),
                            this.loadStats()
                        ]);
                    }
                }
            } catch (err) {
                console.warn('Scheduler check failed:', err);
            }
        },

        async triggerRefresh() {
            if (this.isSyncing || this.scheduler.is_syncing) return;
            this.isSyncing = true;
            try {
                await fetch('/api/refresh', { method: 'POST' });
                this.scheduler.is_syncing = true;
                
                const pollInterval = setInterval(async () => {
                    const statusRes = await fetch('/api/scheduler/status');
                    if (statusRes.ok) {
                        const statusData = await statusRes.json();
                        this.scheduler = statusData;
                        if (!statusData.is_syncing) {
                            clearInterval(pollInterval);
                            this.isSyncing = false;
                            await Promise.all([
                                this.loadNews(),
                                this.loadTopics(),
                                this.loadStats()
                            ]);
                        }
                    }
                }, 2000);
            } catch (err) {
                console.error('Refresh failed:', err);
                this.isSyncing = false;
            }
        },

        setTopic(topicName) {
            this.selectedTopic = (this.selectedTopic === topicName) ? '' : topicName;
            this.loadNews(true);
        },

        setSort(sortValue) {
            if (this.sortBy === sortValue) return;
            this.sortBy = sortValue;
            this.loadNews(true);
        },

        onSearchInput() {
            clearTimeout(this.searchDebounceTimer);
            this.searchDebounceTimer = setTimeout(() => {
                this.loadNews(true);
            }, 250);
        },

        clearFilters() {
            this.selectedTopic = '';
            this.searchQuery = '';
            this.minScore = '';
            this.sortBy = 'importance';
            this.showSavedOnly = false;
            this.loadNews(true);
        },

        toggleBookmark(articleId, event) {
            if (event) event.stopPropagation();
            const idx = this.savedArticleIds.indexOf(articleId);
            if (idx >= 0) {
                this.savedArticleIds.splice(idx, 1);
            } else {
                this.savedArticleIds.push(articleId);
            }
            localStorage.setItem('devpulse_saved', JSON.stringify(this.savedArticleIds));
        },

        isBookmarked(articleId) {
            return this.savedArticleIds.includes(articleId);
        },

        toggleSavedOnly() {
            this.showSavedOnly = !this.showSavedOnly;
            this.loadNews(true);
        },

        openReader(article) {
            this.readingArticle = article;
            document.body.style.overflow = 'hidden';
        },

        closeReader() {
            this.readingArticle = null;
            document.body.style.overflow = '';
        },

        goToPage(p) {
            if (p < 1 || p > this.totalPages || p === this.page) return;
            this.page = p;
            this.loadNews(false);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        getImpactBadge(score) {
            if (score >= 75) {
                return {
                    label: 'Crítico / Disruptivo',
                    classes: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20',
                    dotClass: 'bg-rose-500',
                    barColor: '#f43f5e'
                };
            } else if (score >= 50) {
                return {
                    label: 'Relevancia Alta',
                    classes: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
                    dotClass: 'bg-amber-500',
                    barColor: '#f59e0b'
                };
            } else {
                return {
                    label: 'Incremental / Patch',
                    classes: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700',
                    dotClass: 'bg-emerald-500',
                    barColor: '#10b981'
                };
            }
        },

        getTopicStyle(topic) {
            return 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 font-medium';
        },

        formatRelativeTime(isoString) {
            if (!isoString) return 'reciente';
            const date = new Date(isoString);
            const now = new Date();
            const diffSec = Math.floor((now - date) / 1000);

            if (this.currentLang === 'es') {
                if (diffSec < 60) return 'hace momentos';
                if (diffSec < 3600) return `hace ${Math.floor(diffSec / 60)} min`;
                if (diffSec < 86400) return `hace ${Math.floor(diffSec / 3600)} h`;
                return `hace ${Math.floor(diffSec / 86400)} d`;
            } else {
                if (diffSec < 60) return 'just now';
                if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
                if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
                return `${Math.floor(diffSec / 86400)}d ago`;
            }
        },

        formatMinutesToNext(nextRunIso) {
            if (!nextRunIso) return (this.currentLang === 'es') ? 'en espera' : 'pending';
            const next = new Date(nextRunIso);
            const now = new Date();
            const diffMin = Math.ceil((next - now) / 60000);
            if (diffMin <= 0) return (this.currentLang === 'es') ? 'en curso' : 'in progress';
            return `~${diffMin} min`;
        },

        // Feed Manager Methods
        async openFeedManager() {
            this.showFeedModal = true;
            this.feedMessage = '';
            document.body.style.overflow = 'hidden';
            await this.loadFeeds();
        },

        closeFeedManager() {
            this.showFeedModal = false;
            document.body.style.overflow = '';
        },

        async loadFeeds() {
            try {
                const res = await fetch('/api/feeds');
                if (res.ok) {
                    const data = await res.json();
                    this.systemFeeds = data.system_feeds || [];
                    this.customFeeds = data.custom_feeds || [];
                }
            } catch (err) {
                console.error('Error fetching feeds:', err);
            }
        },

        async addCustomFeed() {
            if (!this.newFeedUrl.trim()) {
                this.feedMessage = 'Ingresa una URL válida para el feed RSS.';
                this.feedMessageType = 'error';
                return;
            }
            this.isAddingFeed = true;
            this.feedMessage = '';
            try {
                const res = await fetch('/api/feeds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.newFeedName.trim() || 'Feed RSS',
                        url: this.newFeedUrl.trim(),
                        topic: this.newFeedTopic
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Error al validar el feed.');
                }
                this.feedMessage = data.message || 'Feed agregado exitosamente.';
                this.feedMessageType = 'success';
                this.newFeedName = '';
                this.newFeedUrl = '';
                await this.loadFeeds();
                this.checkSchedulerStatus();
            } catch (err) {
                this.feedMessage = err.message || 'Error al agregar la fuente.';
                this.feedMessageType = 'error';
            } finally {
                this.isAddingFeed = false;
            }
        },

        async deleteFeed(feedId) {
            if (!confirm('¿Eliminar esta fuente RSS personalizada?')) return;
            try {
                const res = await fetch(`/api/feeds/${feedId}`, { method: 'DELETE' });
                if (res.ok) {
                    this.customFeeds = this.customFeeds.filter(f => f.id !== feedId);
                    this.feedMessage = 'Fuente eliminada correctamente.';
                    this.feedMessageType = 'success';
                }
            } catch (err) {
                console.error('Error deleting feed:', err);
            }
        },

        async toggleFeedActive(feed) {
            const newStatus = !feed.is_active;
            try {
                const res = await fetch(`/api/feeds/${feed.id}/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_active: newStatus })
                });
                if (res.ok) {
                    feed.is_active = newStatus;
                }
            } catch (err) {
                console.error('Error toggling feed:', err);
            }
        },

        // Export Digest (Markdown or JSON)
        async exportDigest(format = 'markdown') {
            let targetArticles = [];
            if (this.savedArticleIds.length > 0) {
                targetArticles = this.articles.filter(a => this.savedArticleIds.includes(a.id));
                if (targetArticles.length === 0) {
                    targetArticles = this.articles;
                }
            } else {
                targetArticles = this.articles;
            }

            if (!targetArticles || targetArticles.length === 0) {
                alert(this.t('saved_empty_export'));
                return;
            }

            const today = new Date().toISOString().split('T')[0];

            if (format === 'json') {
                const jsonStr = JSON.stringify({
                    generator: 'DevPulse Tech Radar',
                    exported_at: new Date().toISOString(),
                    total_articles: targetArticles.length,
                    articles: targetArticles
                }, null, 2);

                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `DevPulse_Digest_${today}.json`;
                a.click();
                URL.revokeObjectURL(url);
                return;
            }

            // Generate Markdown briefing
            let md = `# DevPulse — Technical Briefing & Software Digest\n`;
            md += `> **Fecha:** ${today} | **Idioma:** ${this.currentLang.toUpperCase()} | **Total Novedades:** ${targetArticles.length}\n\n`;
            md += `## 📌 Índice de Contenidos\n\n`;

            targetArticles.forEach((art, i) => {
                md += `${i + 1}. [${art.title}](#story-${art.id}) — *${art.topic}* (Impacto: ${art.importance_score}/100)\n`;
            });

            md += `\n---\n\n## ⚡ Novedades y Diálogos Explicativos\n\n`;

            targetArticles.forEach((art, i) => {
                md += `### <a id="story-${art.id}"></a>${i + 1}. ${art.title}\n\n`;
                md += `- **Fuente:** ${art.source_name}\n`;
                md += `- **Tópico:** ${art.topic}\n`;
                md += `- **Puntuación de Impacto:** ${art.importance_score}/100\n`;
                md += `- **Seguridad:** ${art.safety_status} (${art.safety_score}/100)\n\n`;

                if (art.explanatory_dialogue) {
                    md += `#### 💬 Diálogo Explicativo\n\n${art.explanatory_dialogue}\n\n`;
                }

                if (art.summary_bullets && art.summary_bullets.length > 0) {
                    md += `#### 📌 Ideas Principales (Lectura en 15 Segundos)\n\n`;
                    art.summary_bullets.forEach(b => {
                        md += `- ${b}\n`;
                    });
                    md += `\n`;
                }

                md += `🔗 **Enlace Oficial:** [${art.source_url}](${art.source_url})\n\n`;
                md += `---\n\n`;
            });

            md += `*Generado automáticamente por DevPulse — El Radar Autónomo de Software.*\n`;

            const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `DevPulse_Briefing_${today}.md`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };
};
