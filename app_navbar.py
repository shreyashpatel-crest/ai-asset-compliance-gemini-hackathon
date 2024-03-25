import streamlit as st


def load_navbar(index):
    active_tab = ["", "", ""]
    active_tab[index] = "active"
    st.markdown(
        """
        <style>
            #navbarDropdown:focus-within + .dropdown-menu {
                display: block;
            }
            .appview-container > section > div
            {
                padding-top: 0rem;
                z-index: 999999;
            }
            header
            {
                display: none !important;
            }
            .navbar-light .navbar-nav .active>.nav-link, .navbar-light .navbar-nav .nav-link.active, .navbar-light .navbar-nav .nav-link.show, .navbar-light .navbar-nav .show>.nav-link
            {
                color: #0068c9 !important;
                font-family: Montserrat;
            }
            nav .navbar-nav li a:hover{
                color: #0068c9 !important;
            }
            nav .navbar-nav li a:active{
                color: #0068c9 !important;
            }
            .navbar-nav > li
            {
                margin-left: 0.5em;
                font-family: Montserrat;
            }
            .navbar
            {
                padding-top: 0px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
          <link href='https://fonts.googleapis.com/css?family=Montserrat' rel='stylesheet'>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <nav class="navbar fixed-top navbar-expand-lg navbar-light bg-light">
      <a class="navbar-brand" href="/" target="_self">
        <img src="https://i.ibb.co/gygrCLf/crest-icon.png" width="20" height="30" alt="">
      </a>
      <a class="navbar-brand" href="/" target="_self" style="color:#766c66; font-family: Montserrat;">Asset Compliance AI</a>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item {active_tab[0]}">
            <a class="nav-link" href="/" target="_self">Dashboard<span class="sr-only">(current)</span></a>
          </li>
          <li class="nav-item {active_tab[1]}">
            <a class="nav-link" href="/licenses" target="_self">Licenses</a>
          </li>
        </ul>
      </div>

      <ul class="navbar-nav mr-auto">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                  Administrator
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown" ml-auto>
              <a class="dropdown-item" href="#">Settings</a>
              <a class="dropdown-item" href="#">Log out</a>
            </div>
          </li>
      </ul>
    </nav>
    """,
        unsafe_allow_html=True,
    )
