module NcConfigsController

using Genie, Genie.Renderer, Genie.Renderer.Html, SearchLight, NcConfigs

function index()
  html(:ncconfigs, :index, ncconfigs = rand(NcConfig))
end

function search()
  ncconfigs = find(NcConfig,
              SQLWhereExpression("name LIKE ? OR cm LIKE ? OR parameters LIKE ?",
                                  repeat(['%' * params(:search_ncconfigs) * '%'], 4)))

  html(:ncconfigs, :index, ncconfigs = ncconfigs)
end

end
