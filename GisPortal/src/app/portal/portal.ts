import {

  AfterViewInit,

  Component,

  DestroyRef,

  ElementRef,

  OnDestroy,

  ViewChild,

  inject,

  signal,

} from '@angular/core';

import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { FormsModule } from '@angular/forms';

import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

import { Subject, catchError, debounceTime, distinctUntilChanged, empty, filter, switchMap, tap } from 'rxjs';



import { ChatMessage } from '../models/chat.model';

import { Place } from '../models/place.model';

import { AgentService } from '../services/agent.service';

import { GisApiService } from '../services/gis-api.service';

import { MapService } from '../services/map.service';
import { RuntimeConfigService } from '../config/runtime-config.service';
import { formatChatMessageHtml } from '../utils/chat-message.formatter';
import { getCoordinates, getPlaceId, placesSummary } from '../utils/place.utils';



@Component({

  selector: 'app-portal',

  imports: [FormsModule],

  templateUrl: './portal.html',

  styleUrl: './portal.css',

})

export class PortalComponent implements AfterViewInit, OnDestroy {

  @ViewChild('mapContainer') private mapContainer?: ElementRef<HTMLDivElement>;



  private readonly gisApi = inject(GisApiService);

  private readonly agentApi = inject(AgentService);

  private readonly mapService = inject(MapService);

  private readonly config = inject(RuntimeConfigService);

  private readonly sanitizer = inject(DomSanitizer);

  private readonly destroyRef = inject(DestroyRef);

  private readonly searchInput$ = new Subject<string>();



  protected searchQuery = '';

  protected aiQuery = '';

  protected readonly searchLoading = signal(false);

  protected readonly aiLoading = signal(false);

  protected readonly searchError = signal<string | null>(null);

  protected readonly aiError = signal<string | null>(null);

  protected readonly resultCount = signal(0);

  protected readonly chatMessages = signal<ChatMessage[]>([]);



  private agentSessionId: string | null = null;



  protected readonly placesSummary = placesSummary;



  constructor() {

    this.searchInput$

      .pipe(

        debounceTime(this.config.searchDebounceMs),

        distinctUntilChanged(),

        tap((query) => {

          if (query.length < this.config.searchMinLength) {

            this.searchLoading.set(false);

            this.searchError.set(null);

            this.resultCount.set(0);

            this.mapService.clearMarkers();

          }

        }),

        filter((query) => query.length >= this.config.searchMinLength),

        tap(() => {

          this.searchLoading.set(true);

          this.searchError.set(null);

        }),

        switchMap((query) =>

          this.gisApi.searchPlaces(query).pipe(

            catchError(() => {

              this.searchLoading.set(false);

              this.searchError.set('Name search failed. Check the GIS API connection.');

              return empty();

            }),

          ),

        ),

        takeUntilDestroyed(this.destroyRef),

      )

      .subscribe({

        next: (response) => {

          this.searchLoading.set(false);

          this.resultCount.set(response.total);

          if (!this.mapService.showPlaces(response.items)) {

            this.searchError.set(`No places found for "${this.searchQuery.trim()}".`);

            return;

          }

          this.searchError.set(null);

        },

      });

  }



  ngAfterViewInit(): void {

    if (this.mapContainer) {

      this.mapService.attach(this.mapContainer.nativeElement);

    }

  }



  ngOnDestroy(): void {

    this.mapService.destroy();

  }



  protected onSearchInput(value: string): void {

    this.searchQuery = value;

    this.searchInput$.next(value.trim());

  }



  protected onAiKeydown(event: KeyboardEvent): void {

    if (event.key === 'Enter' && !event.shiftKey) {

      event.preventDefault();

      this.askAgent();

    }

  }



  protected askAgent(): void {

    const query = this.aiQuery.trim();

    if (!query || this.aiLoading()) {

      return;

    }



    this.aiLoading.set(true);

    this.aiError.set(null);

    this.chatMessages.update((messages) => [...messages, { role: 'user', content: query }]);

    this.aiQuery = '';



    this.agentApi

      .ask(query, this.agentSessionId)

      .pipe(takeUntilDestroyed(this.destroyRef))

      .subscribe({

        next: (response) => {

          this.aiLoading.set(false);

          this.agentSessionId = response.session_id;

          this.chatMessages.update((messages) => [

            ...messages,

            {

              role: 'assistant',

              content: response.answer,

              places: response.places,

              total: response.total,

            },

          ]);

          if (response.places.length > 0) {

            this.resultCount.set(response.total ?? response.places.length);

            this.mapService.showPlaces(response.places);

          }

        },

        error: () => {

          this.aiLoading.set(false);

          this.aiError.set('AI search failed. Is the GIS Agent server running?');

        },

      });

  }



  protected resetChat(): void {

    if (this.agentSessionId) {

      this.agentApi.reset(this.agentSessionId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe();

    }

    this.agentSessionId = null;

    this.chatMessages.set([]);

    this.aiError.set(null);

  }



  protected formatMessage(content: string): SafeHtml {

    return this.sanitizer.bypassSecurityTrustHtml(formatChatMessageHtml(content));

  }



  protected isSelectedPlace(place: Place): boolean {

    return this.mapService.isSelected(place);

  }



  protected selectPlaceFromMessage(place: Place, messagePlaces: Place[]): void {

    const coords = getCoordinates(place);

    if (coords) {

      this.mapService.syncPlaces(messagePlaces);

      this.mapService.focusPlace(place);

      return;

    }



    this.gisApi

      .getPlace(getPlaceId(place))

      .pipe(takeUntilDestroyed(this.destroyRef))

      .subscribe({

        next: (fullPlace) => {

          this.mapService.syncPlaces(

            messagePlaces.map((item) => (getPlaceId(item) === getPlaceId(fullPlace) ? fullPlace : item)),

          );

          this.mapService.focusPlace(fullPlace);

        },

        error: () => {

          this.aiError.set('Could not load place details for the map.');

        },

      });

  }

}


