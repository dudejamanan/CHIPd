function renderSettings() {

    return `

        <div class="page-header">

            <div>

                <div class="eyebrow">
                    SYSTEM CONFIGURATION
                </div>

                <h1>
                    Settings
                </h1>

                <p>
                    Configure the local CHIPd development environment.
                </p>

            </div>

        </div>


        <section class="settings-grid">

            <div class="panel settings-card">

                <div class="panel-header">

                    <div>

                        <h2>
                            Backend
                        </h2>

                        <p>
                            Local API configuration
                        </p>

                    </div>

                </div>


                <div class="settings-content">

                    <div class="setting-row">

                        <div>

                            <strong>
                                API Endpoint
                            </strong>

                            <span>
                                Backend server URL
                            </span>

                        </div>

                        <code>
                            http://localhost:8000
                        </code>

                    </div>


                    <div class="setting-row">

                        <div>

                            <strong>
                                Connection
                            </strong>

                            <span>
                                Backend availability
                            </span>

                        </div>

                        <span class="settings-status">
                            ● Connected
                        </span>

                    </div>

                </div>

            </div>


            <div class="panel settings-card">

                <div class="panel-header">

                    <div>

                        <h2>
                            Hardware
                        </h2>

                        <p>
                            Default HDL configuration
                        </p>

                    </div>

                </div>


                <div class="settings-content">

                    <div class="setting-row">

                        <div>

                            <strong>
                                Default HDL
                            </strong>

                            <span>
                                Language used for generated RTL
                            </span>

                        </div>

                        <span>
                            SystemVerilog
                        </span>

                    </div>


                    <div class="setting-row">

                        <div>

                            <strong>
                                Simulator
                            </strong>

                            <span>
                                Local verification engine
                            </span>

                        </div>

                        <span>
                            Icarus Verilog
                        </span>

                    </div>

                </div>

            </div>

        </section>

    `;

}