library(shiny)
library(shinydashboard)
library(shinyjs)
library(readxl)
library(dplyr)
library(leaflet)
library(DT)
library(bslib)

ui <- dashboardPage(
  skin = "green",
  dashboardHeader(title = "Threatened Species Explorer 🦁"),
  dashboardSidebar(
    width = 250,
    useShinyjs(),
    div(style = "padding: 15px;",
        textInput("searchInput", "🔍 Quick Search", placeholder = "Search any field...")
    ),
    sidebarMenu(
      id = "sidebarmenu",
      menuItem("🧬 Taxonomy", tabName = "taxonomy",
        selectInput("phylumFilter", "Phylum", choices = NULL, selectize = TRUE),
        selectInput("classFilter", "Class", choices = NULL, selectize = TRUE),
        selectInput("speciesFilter", "Species", choices = NULL, selectize = TRUE)
      ),
      menuItem("🌍 Location", tabName = "location",
        selectInput("continentFilter", "Continent", choices = NULL, selectize = TRUE),
        selectInput("countryFilter", "Country", choices = NULL, selectize = TRUE),
        selectInput("stateFilter", "State", choices = NULL, selectize = TRUE),
        selectInput("countyFilter", "County", choices = NULL, selectize = TRUE),
        selectInput("landcoverFilter", "Landcover", choices = NULL, selectize = TRUE)
      ),
      menuItem("🏷️ Status", tabName = "status",
        selectInput("iucnFilter", "IUCN Status", choices = NULL, selectize = TRUE)
      )
    ),
    div(style = "padding: 15px; display: flex; justify-content: center;",
        actionButton("resetFilters", "🔄 Reset All",
                     style = "background-color: #605ca8; color: white;")
    )
  ),
  dashboardBody(
    theme = bs_theme(bootswatch = "minty"),
    tabsetPanel(
      tabPanel("🗺️ Map",
        fluidRow(
          valueBoxOutput("speciesBox", width = 3),
          valueBoxOutput("observationBox", width = 3),
          valueBoxOutput("countryBox", width = 3),
          valueBoxOutput("iucnBox", width = 3)
        ),
        box(
          width = 12,
          status = "success",
          solidHeader = TRUE,
          leafletOutput("map", height = 600)
        )
      ),
      tabPanel("📊 Data",
        fluidRow(
          column(12,
            box(
              width = NULL,
              title = "Filtered Data",
              status = "success",
              solidHeader = TRUE,
              downloadButton("downloadData", "📥 Download Data"),
              br(), br(),
              DTOutput("dataTable")
            )
          )
        )
      ),
      tabPanel("ℹ️ Info",
        fluidRow(
          column(12,
            box(
              width = NULL,
              title = "About This Dataset",
              status = "info",
              solidHeader = TRUE,
              h4("🦁 Wildlife Occurrence Data"),
              p("This dataset contains wildlife occurrence records with the following information:"),
              tags$ul(
                tags$li(icon("dna"), " Taxonomic classification from Phylum to Species"),
                tags$li(icon("globe"), " Geographic location including continent, country, state, and county"),
                tags$li(icon("tag"), " IUCN conservation status"),
                tags$li(icon("map-marker-alt"), " Precise coordinates of sightings"),
                tags$li(icon("leaf"), " Landcover type")
              ),
              h4("📍 How to Use"),
              tags$ul(
                tags$li("Use the quick search to find specific records"),
                tags$li("Apply filters to narrow down the data"),
                tags$li("View locations on the map"),
                tags$li("Download filtered data for further analysis")
              )
            )
          )
        )
      )
    )
  )
)

server <- function(input, output, session) {
  wildlife_data <- reactive({
    read_excel("occurrence_filtered_final.xlsx") %>%
      rename(longitude = lon_keep, latitude = lat_keep) %>%
      filter(!is.na(longitude) & !is.na(latitude))
  })
  observe({
    data <- wildlife_data()
    updateSelectInput(session, "phylumFilter", choices = c("All", sort(unique(data$phylum))))
    updateSelectInput(session, "classFilter", choices = c("All", sort(unique(data$class))))
    updateSelectInput(session, "speciesFilter", choices = c("All", sort(unique(data$species))))
    updateSelectInput(session, "continentFilter", choices = c("All", sort(unique(data$continent))))
    updateSelectInput(session, "countryFilter", choices = c("All", sort(unique(data$countryCode))))
    updateSelectInput(session, "stateFilter", choices = c("All", sort(unique(data$state))))
    updateSelectInput(session, "countyFilter", choices = c("All", sort(unique(data$county))))
    updateSelectInput(session, "landcoverFilter", choices = c("All", sort(unique(data$landcover))))
    updateSelectInput(session, "iucnFilter", choices = c("All", sort(unique(data$iucnRedListCategory))))
  })
  filtered_data <- reactive({
    data <- wildlife_data()
    if (!is.null(input$searchInput) && input$searchInput != "") {
      s <- tolower(input$searchInput)
      data <- data %>%
        filter(
          grepl(s, tolower(species)) |
            grepl(s, tolower(phylum)) |
            grepl(s, tolower(class)) |
            grepl(s, tolower(state)) |
            grepl(s, tolower(countryCode)) |
            grepl(s, tolower(county)) |
            grepl(s, tolower(landcover)) |
            grepl(s, tolower(iucnRedListCategory))
        )
    }
    if (input$phylumFilter != "All") data <- data %>% filter(phylum == input$phylumFilter)
    if (input$classFilter != "All") data <- data %>% filter(class == input$classFilter)
    if (input$speciesFilter != "All") data <- data %>% filter(species == input$speciesFilter)
    if (input$continentFilter != "All") data <- data %>% filter(continent == input$continentFilter)
    if (input$countryFilter != "All") data <- data %>% filter(countryCode == input$countryFilter)
    if (input$stateFilter != "All") data <- data %>% filter(state == input$stateFilter)
    if (input$countyFilter != "All") data <- data %>% filter(county == input$countyFilter)
    if (input$landcoverFilter != "All") data <- data %>% filter(landcover == input$landcoverFilter)
    if (input$iucnFilter != "All") data <- data %>% filter(iucnRedListCategory == input$iucnFilter)
    data
  })
  output$speciesBox <- renderValueBox({
    valueBox(length(unique(filtered_data()$species)), "Species 🦁", color = "green")
  })
  output$observationBox <- renderValueBox({
    valueBox(nrow(filtered_data()), "Observations 📍", color = "yellow")
  })
  output$countryBox <- renderValueBox({
    valueBox(length(unique(filtered_data()$countryCode)), "Countries 🌍", color = "purple")
  })
  output$iucnBox <- renderValueBox({
    valueBox(
      paste(names(sort(table(filtered_data()$iucnRedListCategory), decreasing = TRUE)[1])),
      "Most Common Status ⚠️",
      color = "red"
    )
  })
  output$map <- renderLeaflet({
    leaflet() %>%
      addProviderTiles(providers$CartoDB.Positron) %>%
      setView(lng = -95, lat = 40, zoom = 4)
  })
  observe({
    data <- filtered_data()
    pal <- colorFactor(
      palette = c("green", "yellow", "orange", "red", "purple"),
      domain = unique(data$iucnRedListCategory)
    )
    popup_content <- paste0(
      "<strong>🦁 ", data$species, "</strong><br>",
      "🧬 ", data$phylum, " - ", data$class, "<br>",
      "📍 ", data$county, ", ", data$state, ", ", data$countryCode, "<br>",
      "🌱 Landcover: ", data$landcover, "<br>",
      "⚠️ IUCN: ", data$iucnRedListCategory
    )
    leafletProxy("map", data = data) %>%
      clearMarkers() %>%
      addCircleMarkers(
        lng = ~longitude,
        lat = ~latitude,
        color = ~pal(iucnRedListCategory),
        popup = popup_content,
        radius = 6,
        fillOpacity = 0.8
      )
  })
  output$dataTable <- renderDT({
    datatable(
      filtered_data(),
      options = list(pageLength = 10, scrollX = TRUE),
      selection = "single"
    )
  })
  output$downloadData <- downloadHandler(
    filename = function() {
      paste("wildlife-data-", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(filtered_data(), file, row.names = FALSE)
    }
  )
  observeEvent(input$resetFilters, {
    updateTextInput(session, "searchInput", value = "")
    updateSelectInput(session, "phylumFilter", selected = "All")
    updateSelectInput(session, "classFilter", selected = "All")
    updateSelectInput(session, "speciesFilter", selected = "All")
    updateSelectInput(session, "continentFilter", selected = "All")
    updateSelectInput(session, "countryFilter", selected = "All")
    updateSelectInput(session, "stateFilter", selected = "All")
    updateSelectInput(session, "countyFilter", selected = "All")
    updateSelectInput(session, "landcoverFilter", selected = "All")
    updateSelectInput(session, "iucnFilter", selected = "All")
  })
}

shinyApp(ui, server)
