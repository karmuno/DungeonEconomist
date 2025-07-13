# DungeonEconomist Application Process Flow

This document describes the overall flow of the DungeonEconomist application, highlighting how different pages are rendered and how modals are loaded and interact with the DOM using HTMX.

## 1. Core Application Flow

The application is built with FastAPI for the backend and Jinja2 templates with HTMX for the frontend, providing a dynamic single-page application feel.

### Main Pages:

*   **Home Page (`/`)**:
    *   **Endpoint:** `GET /` (function `index` in `app/main.py`)
    *   **Template:** `index.html`
    *   **Content:** Displays overall game statistics (adventurer count, party count, expedition count), recent expeditions, player treasury, total score, current game time, active expeditions, and unavailable adventurers.
    *   **Dynamic Elements:** Includes `partials/time_panel.html` which is dynamically updated.

*   **Adventurers Page (`/adventurers`)**:
    *   **Endpoint:** `GET /adventurers` (function `adventurers_page` in `app/main.py`)
    *   **Template:** `adventurers.html`
    *   **Content:** Lists all adventurers.
    *   **Dynamic Elements:** Includes `partials/adventurer_list.html`.

*   **Parties Page (`/parties`)**:
    *   **Endpoint:** `GET /parties` (function `parties_page` in `app/main.py`)
    *   **Template:** `parties.html`
    *   **Content:** Lists all parties.
    *   **Dynamic Elements:** Includes `partials/party_list_container.html`, which can be filtered and sorted dynamically.

*   **Expeditions Page (`/expeditions`)**:
    *   **Endpoint:** `GET /expeditions` (function `expeditions_page` in `app/main.py`)
    *   **Template:** `expeditions.html`
    *   **Content:** Displays active expeditions and provides forms to launch new ones.
    *   **Dynamic Elements:** Includes `partials/time_panel.html` and `partials/active_expeditions.html`.

## 2. Modal Interactions

Modals in DungeonEconomist are primarily loaded via HTMX requests, where a button or link triggers a `hx-get` request to a FastAPI endpoint. This endpoint returns an HTML partial, which is then swapped into a designated modal container in the DOM.

### General Modal Structure:

The main `base.html` template (which all other pages extend) likely contains a hidden modal container:

```html
<div id="modal" class="fixed inset-0 bg-gray-900 bg-opacity-50 hidden flex items-center justify-center z-50">
    <div id="modal-content" class="bg-gray-800 p-6 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto relative">
        <!-- Modal content will be loaded here -->
    </div>
</div>
```

When a modal is triggered, the `hx-target="#modal-content"` attribute directs the response to be swapped into this `div`. JavaScript is then used to make the `#modal` div visible.

### Specific Modal Flows:

#### 2.1. Create Party Modal

*   **Trigger:** "Create New Party" button on the `/parties` page.
    *   **HTMX Attributes:** `hx-get="/parties/create-form"` `hx-target="#modal-content"` `hx-swap="innerHTML"` `onclick="document.getElementById('modal').classList.remove('hidden')"`
*   **Backend Endpoint:** `GET /parties/create-form` (function `party_create_form` in `app/main.py`)
*   **Template Rendered:** `partials/party_form.html`
*   **Content Replaced/Inserted:** The content of `partials/party_form.html` (which now handles both creation and editing) is loaded into the `#modal-content` div.
*   **Form Submission:**
    *   **HTMX Attributes:** The form within `partials/party_form.html` has `hx-post="/parties/"` `hx-target="#party-list-container"` `hx-swap="innerHTML"` `hx-on:htmx:after-request="document.getElementById('modal').classList.add('hidden'); document.body.dispatchEvent(new Event('partyListChanged'))"`
    *   **Backend Endpoint:** `POST /parties/` (function `create_party` in `app/main.py`)
    *   **Response:** The `create_party` function returns an `HX-Redirect` header to `/parties/{new_party.id}/edit-form`. This causes HTMX to make a new request to that URL.

#### 2.2. Edit Party Modal

*   **Trigger:** "Edit Party" button for a specific party on the `/parties` page.
    *   **HTMX Attributes:** `hx-get="/parties/{{ party.id }}/edit-form"` `hx-target="#modal-content"` `hx-swap="innerHTML"` `onclick="document.getElementById('modal').classList.remove('hidden')"`
*   **Backend Endpoint:** `GET /parties/{party_id}/edit-form` (function `party_edit_form` in `app/main.py`)
*   **Template Rendered:** `partials/party_form.html`
*   **Content Replaced/Inserted:** The content of `partials/party_form.html` (pre-populated with party data, players, and available adventurers) is loaded into the `#modal-content` div.
*   **Form Submission:**
    *   **HTMX Attributes:** The form within `partials/party_form_enhanced.html` has `hx-put="/parties/{{ party.id }}"` `hx-target="#party-list-container"` `hx-swap="innerHTML"` `hx-on:htmx:after-request="document.getElementById('modal').classList.add('hidden'); document.body.dispatchEvent(new Event('partyListChanged'))"`
    *   **Backend Endpoint:** `PUT /parties/{party_id}` (function `update_party` in `app/main.py`)
    *   **Response:** The `update_party` function returns a `PartyOut` JSON response. However, due to the `hx-target` and `hx-swap` on the form, the entire `#party-list-container` on the main `/parties` page is reloaded (likely via a separate `hx-get` triggered by `partyListChanged` event or similar mechanism not explicitly shown in the provided snippets but implied by the `hx-target`).

#### 2.3. Add Adventurers to Party Modal (within Edit Party Modal)

This modal is *nested* within the "Edit Party" modal.

*   **Trigger:** This is part of the `partials/party_form_enhanced.html` template. The "Add Adventurers" section within this form.
*   **Backend Endpoint:** `GET /parties/{party_id}/add-member-form` (function `party_add_member_form` in `app/main.py`)
*   **Template Rendered:** `partials/add_party_member_enhanced.html`
*   **Content Replaced/Inserted:** The content of `partials/add_party_member_enhanced.html` is loaded into a specific `div` within `partials/party_form_enhanced.html` (likely `#add-member-container`).
*   **Adding an Adventurer (Form Submission within the modal):**
    *   **HTMX Attributes:** Each adventurer card in `partials/add_party_member_enhanced.html` has a form with `hx-post="/parties/add-member/"` `hx-target="#modal-content"` `hx-swap="innerHTML"`.
    *   **Backend Endpoint:** `POST /parties/add-member/` (function `add_adventurer_to_party` in `app/main.py`)
    *   **Response:** If the request is an HTMX request (checked by `request.headers.get("HX-Request")`), the `add_adventurer_to_party` function *re-renders the entire `party_edit_form`* by calling `party_edit_form(request, party.id, db)`. This effectively refreshes the entire "Edit Party" modal content, including the updated list of party members and available adventurers.

#### 2.4. Create Adventurer Modal

*   **Trigger:** "Create New Adventurer" button on the `/adventurers` page or within the "No available adventurers" message in the "Add Adventurers" modal.
    *   **HTMX Attributes:** `hx-get="/adventurers/create-form"` `hx-target="#modal-content"` `hx-swap="innerHTML"` `onclick="document.getElementById('modal').classList.remove('hidden')"`
*   **Backend Endpoint:** `GET /adventurers/create-form` (function `adventurer_create_form` in `app/main.py`)
*   **Template Rendered:** `partials/adventurer_form.html`
*   **Content Replaced/Inserted:** The content of `partials/adventurer_form.html` is loaded into the `#modal-content` div.

#### 2.5. Create Expedition Modal

*   **Trigger:** "Launch Expedition" button on the `/expeditions` page.
    *   **HTMX Attributes:** `hx-get="/expeditions/create-form"` `hx-target="#modal-content"` `hx-swap="innerHTML"` `onclick="document.getElementById('modal').classList.remove('hidden')"`
*   **Backend Endpoint:** `GET /expeditions/create-form` (function `expedition_create_form` in `app/main.py`)
*   **Template Rendered:** `partials/expedition_form.html`
*   **Content Replaced/Inserted:** The content of `partials/expedition_form.html` is loaded into the `#modal-content` div.

## 3. Dynamic Content Updates (Non-Modal)

Beyond modals, HTMX is used extensively for partial updates:

*   **Party List Filtering/Sorting (`/parties` page):**
    *   **Trigger:** Changing filter/sort dropdowns.
    *   **HTMX Attributes:** `hx-get="/ui/get-party-list"` `hx-target="#party-list-container"` `hx-swap="innerHTML"`
    *   **Backend Endpoint:** `GET /ui/get-party-list` (function `get_party_list_html` in `app/main.py`)
    *   **Content Replaced:** The entire `#party-list-container` is replaced with the updated list of parties.

*   **Time Panel Updates (various pages):**
    *   **Trigger:** "Advance Day" or "Skip Until Ready" buttons.
    *   **HTMX Attributes:** `hx-post="/time/advance-day"` or `hx-post="/time/skip-until-ready"` `hx-target="#time-panel-container"` `hx-swap="innerHTML"`
    *   **Backend Endpoints:** `POST /time/advance-day` (function `advance_day`) or `POST /time/skip-until-ready` (function `skip_until_ready`) in `app/main.py`.
    *   **Content Replaced:** The `#time-panel-container` (which wraps `partials/time_panel.html`) is updated with the new game time and related information.

*   **Active Expeditions List (`/expeditions` page):**
    *   **Trigger:** Likely a polling mechanism or triggered after time advancement.
    *   **HTMX Attributes:** `hx-get="/expeditions/active"` `hx-target="#active-expeditions-container"` `hx-swap="innerHTML"`
    *   **Backend Endpoint:** `GET /expeditions/active` (function `expeditions_active` in `app/main.py`)
    *   **Content Replaced:** The `#active-expeditions-container` is updated with the current list of active expeditions.

This overview should provide a clear understanding of the application's flow and how HTMX facilitates dynamic content loading, especially for modals.