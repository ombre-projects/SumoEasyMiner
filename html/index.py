#!/usr/bin/python
# -*- coding: utf-8 -*-
## Copyright (c) 2017, The Sumokoin Project (www.sumokoin.org)

html = """
<!DOCTYPE html>
<html>
    <head>
        <script src="./scripts/jquery-1.9.1.min.js"></script>
        <script src="./scripts/mustache.min.js"></script>
        <script src="./scripts/jquery.sparkline.js"></script>
        <script src="./scripts/utils.js"></script>
        <script type="text/javascript">

            function app_ready(){
                console.log("Main window ready!");
                app_hub.on_create_sumo_pool_list_event.connect(create_pool_list);

                app_hub.on_update_hashrate_event.connect(updateHashRate);
                app_hub.on_error_event.connect(reportError);

                app_hub.on_back_end_error_event.connect(callback);

                app_hub.on_remove_pool_confirm_event.connect(function(pool_id){
                    $('#' + pool_id).remove();
                });

                app_hub.on_hide_pool_success_event.connect(function(pool_id){
                    $('#' + pool_id).hide();
                });

                app_hub.on_edit_pool_success_event.connect(function(pool_info_json){
                    var pool_info = $.parseJSON(pool_info_json);
                    var el = $('#' + pool_info['id']);
                    el.find(".pool-name").text(pool_info['name']);
                });

                app_hub.on_start_mining_event.connect(function(pool_id){
                    setTimeout(function(){
                        var el = $('#' + pool_id);
                        var num_cpus = el.find(".num_cpus").find(":selected").text();
                        var btn = el.find(".btn-start");
                        var btn_text = btn.find('.btn-start-text');
                        var btn_icon = btn.find('.fa');
                        var status = el.find('.mining-status');
                        var is_mining_elem = el.find('.is-mining');

                        btn_text.text("Stop");
                        btn.addClass('btn-stop');
                        btn_icon.addClass('fa-pause');
                        status.html('<strong>Mining...</strong>');
                        el.addClass('row-active');
                        is_mining_elem.val(1);
                    }, 1);
                });

                app_hub.on_stop_mining_event.connect(function(pool_id){
                    setTimeout(function(){
                        var el = $('#' + pool_id);
                        var num_cpus = el.find(".num_cpus").find(":selected").text();
                        var btn = el.find(".btn-start");
                        var btn_text = btn.find('.btn-start-text');
                        var btn_icon = btn.find('.fa');
                        var status = el.find('.mining-status');
                        var is_mining_elem = el.find('.is-mining');

                        btn_text.text("Start");
                        btn.removeClass('btn-stop');
                        btn_icon.removeClass('fa-pause');
                        el.removeClass('row-active');
                        status.html('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;');
                        el.find('.hashrate').text('0.00 H/s');
                        is_mining_elem.val(0);
                    }, 1);
                });
            }

            function callback(s){
                console.log("Error: " + s);
                alert(s);
            }


            function create_pool_list(pool_list, num_cpus, is_win32){
                var priority_levels = ["idle","low","normal"];
                if(is_win32 == true){
                    priority_levels.push("high", "very high");
                }

                var table_body = $('#pools_table tbody');
                var tmpl = '<option value="{{ i }}">{{ j }}</option>';
                var tmpl2 = '<option selected="true" value="{{ i }}">{{ j }}</option>';
                var select_cpu = num_cpus;
                var option_html = "";
                for(var i=1;i<=num_cpus;i++){
                    if(i == select_cpu) option_html += Mustache.render(tmpl2, {i: i, j: i});
                    else option_html += Mustache.render(tmpl, {i: i, j: i});
                }
                var pool_list = $.parseJSON(pool_list);
                var template = $('#template').html();
                Mustache.parse(template);
                pool_list.forEach(function(pool_info) {

                    var option_html2 = "";
                    priority_levels.forEach(function(level){
                        if(pool_info['priority_level'] == level) option_html2 += Mustache.render(tmpl2, {i: level, j: level.capitalize()});
                        else option_html2 += Mustache.render(tmpl, {i: level, j: level.capitalize()});
                    });

                    var rendered = Mustache.render(template,
                                                    {   'pool_id': pool_info['id'],
                                                        'pool_name': pool_info['name'],
                                                        'algo': pool_info['algo'],
                                                        'option_html': option_html,
                                                        'option_html2': option_html2,
                                                        'pool_removable': pool_info['is_fixed'] ? "none" : "inline-block",
                                                        'pool_hidden': pool_info['is_hidden'] ? "none" : "table-row"
                                                    });


                    table_body.append(rendered);

                    if(pool_info['num_cpus'] != select_cpu){
                        $('#' + pool_info['id']).find('.num_cpus').val(pool_info['num_cpus']);
                    }
                });
            }


            function startStopMining(pool_id){
                var el = $('#' + pool_id);
                var num_cpus = el.find(".num_cpus").find(":selected").text();

                var status = el.find('.mining-status');
                var is_mining_elem = el.find('.is-mining');
                var is_mining_stopped = is_mining_elem.val() == 0;
                status.hide().text( is_mining_stopped ? 'Start mining...': 'Stop mining...' ).fadeIn(500, function(){
                    app_hub.start_stop_mining(pool_id, num_cpus);
                });

                return false;
            }

            function getReadableHashRateString(hashrate){
                var i = 0;
                var byteUnits = [' H/s', ' kH/s', ' MH/s', ' GH/s', ' TH/s', ' PH/s' ];
                while (hashrate > 1000){
                    hashrate = hashrate / 1000;
                    i++;
                }
                return hashrate.toFixed(2) + byteUnits[i];
            }

            var rate_data = {};
            var hashrate_graph_settings = {
                type: 'line',
                width: '80%',
                height: '20%',
                lineColor: '#03a678',
                fillColor: 'rgba(3, 166, 120, .3)',
                spotColor: null,
                minSpotColor: null,
                maxSpotColor: '#99ff33',
                highlightLineColor: '#236d26',
                spotRadius: 3,
                drawNormalOnTop: false,
                chartRangeMin: 0,
                tooltipFormat: '{{y}} H/s',
                tooltipClassname: 'hashrate-tooltip'
            };

            var shares_graph_settings = {
                type: 'pie',
                width: '40%',
                height: '20%',
                borderColor: '#03a678',
                borderWidth: 1,
                sliceColors: ['rgba(3, 166, 120, .3)', 'rgb(220, 57, 18)'],
                drawNormalOnTop: false
            };

            function updateHashRate(mining_info){
                setTimeout(function(){
                    info = $.parseJSON(mining_info);
                    var el = $('#' + info.pool_id);
                    var is_mining_stopped = el.find('.is-mining').val() == 0;
                    if(is_mining_stopped) return;

                    // create hashrate chart
                    if(!(info.pool_id in rate_data)){
                        rate_data[info.pool_id] = [];
                    }
                    var data = rate_data[info.pool_id];

                    if(data.length > 0 || info.hash_rate > 0){
                        if(data.length == 0) data.push(0);
                        if(data.length > 180) data.shift(1);
                        data.push(Math.round10(info.hash_rate, -2));
                    }

                    if(data.length > 0){
                        el.find('.rate-chart').sparkline(data, hashrate_graph_settings);
                    }

                    var sum = 0.0, n = 0, max = 0;
                    for( var i = 0; i < data.length; i++ ){
                        sum += data[i];
                        if(data[i] > 0) n++;
                        if(data[i] > max) max = data[i];
                    }
                    var average = n > 0 ? sum/n : 0.0;

                    el.find('.hashrate').text( getReadableHashRateString(info.hash_rate) );
                    el.find('.hashrate-avg').text( getReadableHashRateString(average) );
                    el.find('.hashrate-max').text( getReadableHashRateString(max) );

                    if(info.shares_total > 0){
                        el.find('.shares-chart').sparkline([info.shares_good, info.shares_total - info.shares_good], shares_graph_settings);
                    }

                    el.find('.shares').text(info.shares_good + "/" + info.shares_total);
                    el.find('.shares-pct').text(info.shares_pct);
                    el.find('.difficulty').text(info.difficulty);
                }, 1);
            }

            function reportError(pool_id, err){
                setTimeout(function(){
                    var el = $('#' + pool_id);
                    var status = el.find('.mining-status');
                    var is_mining_stopped = el.find('.is-mining').val() == 0;

                    if(err != 'ERROR_END' && !is_mining_stopped){
                        status.html(err).addClass('error-text').hide().fadeIn(600);
                    }
                    else
                    {
                        status.hide().removeClass('error-text');
                        if(!is_mining_stopped){
                            status.text('Mining...').fadeIn(600);
                        }
                    }
                }, 1);
            }

            function changeCPUCores(el, pool_id){
                var s = $(el);
                var num_cpus = s.val();
                app_hub.change_cpus(pool_id, num_cpus);
            }

            function changePriority(el, pool_id){
                var s = $(el);
                var priority_level = s.val();
                app_hub.change_priority(pool_id, priority_level);
            }

            function viewLog(pool_id){
                app_hub.view_log(pool_id);
                return false;
            }

            function hidePool(pool_id){
                app_hub.hide_pool_row(pool_id);
                return false;
            }

            function showAllPools(){
                var tbody = $('#pools_table').find('tbody');
                var hidden_rows = tbody.find('tr').filter(function() {
                    return $(this).css("display") == "none";
                });

                if(hidden_rows.length == 0) return false;

                hidden_rows.show();

                var pool_ids = [];
                hidden_rows.each(function(){
                    pool_ids.push($(this).attr('id'));
                });

                app_hub.show_pools(pool_ids);
                return false;
            }

            function removePool(pool_id){
                app_hub.remove_pool(pool_id);
            }

            function addPool(){
                app_hub.show_addpool_dialog();
                return false;
            }

            function editPool(pool_id){
                app_hub.edit_pool(pool_id);
                return false;
            }

            function quitApp(){
                app_hub.quit_app();
            }

            function open_link(link){
                app_hub.open_link(link);
            }
        </script>

        <link href="./css/bootstrap.min.css" rel="stylesheet">
        <link href="./css/font-awesome.min.css" rel="stylesheet">
        <style type="text/css">
            * {
                -webkit-box-sizing: border-box;
                box-sizing: border-box;
            }

            body {
                -webkit-user-select: none;
                user-select: none;
                cursor: default;
                color: #393a35;
                font-family: "RoboReg", "Helvetica Neue", Helvetica, Arial, sans-serif;
                font-size: 14px;
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }

            .container{
                background-color: #fff;
                background-position: center center;
                background-image: url('data:image/jpeg;base64,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');
            }

            a, a:hover, a:active, a:focus {
                text-decoration: none;
                outline: 0;
                cursor: default;
            }

            a, a:active, a:focus{
                color: #337AB7;
            }

            a:hover{
                color: #333;
            }


            .container{
                padding: 0;
                margin: 5px 0px 5px 20px;
            }

            .btn-start{
                float: left;
                padding-left: 1em;
            }

            .btn-start, .btn-start:active, .btn-start:focus, .btn-start:hover{
                color: #337AB7;
            }

            .btn-start:hover{
                color: #333;
            }

            .btn-stop, .btn-stop:active, .btn-stop:focus, .btn-stop:hover {
                color: #cc3300;
            }

            .btn-stop:hover {
                color: #333;
            }

            table {
                border-spacing: 0;
                border-collapse: collapse;
                font-size: 90%;
            }


            table thead tr{
                height: 4.5em;
            }

            table tbody tr {
                color: #999;
                height: 6em;
                line-height: 1.6em;
                border-top: 1px solid #aaa;
            }

            table thead tr th{
                text-align: center;
                border-bottom: 1px solid #aaa;
                text-size: 18px;
                padding: auto 1em;
            }

            table tr td {
                text-align: center;
            }

            .row-active{
                color: #000;
            }

            .mining-status{
                padding-right: 0.5em;
                padding-left: 0.5em;
                color: #393a35;
                font-size: 100%;
                text-align: right;
            }

            .error-text{
                color: #cc0000;
                font-size: 90%;
                text-align: center;
            }

            .num_cpus, .cpu_priority{
                color: #000;
            }

            .show-all-pools, .show-all-pools:hover, .show-all-pools:focus, .show-all-pools:active {
                font-weight: normal;
            }

            .add-pool .form-control{
                height: 28px;
            }

            .add-pool .btn{
                padding-top: 1px;
                padding-bottom: 1px;
                cursor: default;
                font-size: 12px;
                border-radius: 0;
                height: 22px;
            }

            .add-pool select, .add-pool input {
                font-size: 12px;
                height: 22px;
                color: #333;
            }

            .pool-name{
                font-weight: bold;
            }

            .pool-btns{
                font-weight: normal;
                text-align: right;
                padding-right: 1em;
                border-bottom:none;
                color: #fff;
            }

            .pool-btns a, .pool-btns a:active, .pool-btns a:focus{
                color: #fff;
                font-weight: bold;
                text-shadow: 2px 2px 4px #666;
            }

            .pool-btns a:hover{
                color: #fff;
                text-shadow: none;
            }

            .banner{
                font-weight: normal;
                text-align:left;
                padding-left:8px;
                border-bottom:none;
                background-image-position: left center;
                background-repeat: no-repeat;
                background-image: url('data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAZAAAAAzCAYAAAC5QF44AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAECBJREFUeNrsnX9MVecZx1/FClJRVKRCJ1KpLBNUDFWj1XLVdiao9Rons+uSYmrazK4p2sbWP1YlW7vElNqFxcQmlouz2qEVTQ2mdO0Fqy4iBNaqTbGVu4pQtQqIP6n07Pm+vOf2cDjn3nMv4Nb5fJKXcz3nPT/e99z7PO/z430VgmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmEYhmGY/1sG9NN13VQyqGRZHKukUkdlH3c/wzAMo5NLpYGKhjJhwgQtLi5OfgZHjx7V9GOqXi53GcMwzN0NrI1ag3LQli5dqrlcLu3xxx/3KxBw6NAhoxLR1HkZ3IUMwzA/LQb2wTXgrvIalcCaNWvE8OHDxfjx48XQoUPlvubmZrmdM2eOqKqqMisfr7oOwzAM8xOhtzEQ3fLwEx8fL2JjY0VLS4u4ePGiiImJEe3t7eKzzz4TnZ2dspSVlYlhw4aJvLw88/Wmiq74SK8hYydWPZ9vwIABPn7VDMMw/zsWSKyyHPw89thjYtKkSdLqGDFihNz+8MMP8hj2jx07VowaNUqsWrVKHistLTVf06uuG7bSoLKRCuIrLep6DfTvFipFVJIDnFuq/UhGkPskG+p6LY57VWkx1lPP4LK5pn5Og+GcWrUvTylEY32XFpyNYfZjnuEaeQ7q+5/Z4liP/aZndwe5drDzg7adPuca+lenJdg7YRgmMIN6ce5ms7CHcoDlkZ6eLmjULy2RS5cuiR07dviPo4Cnn35aHDlyRBw7dkzMmDHDqJRw3ZVhCD3dFRbb2tpaU1dXV+zz+ZqSk5MTMzIyFtGz5NIxN9VbQ8/msVGIkjNnzqyjzSoq121u5xd6dK8Y2qRSqTccd6nr7Lp582Y7PicmJmaqZ4Aw89AzmNsozzl37tyBtra2cnwePXp0KhWXOvYUnTeXzms1nnTr1q3mr7/++gOrh6yqqmrCrak0hTE4kFy7du13tNlJ5UKAfjcq5kwqNRZVLfeTRbr9zTffTFu7du3ZIM/U4/wQ2o7nc6n6b+N4VFRUzP333++KjIx0qXey0uZ7wTBMH4MfZLdg+JQpU7SkpCSNBLaWkJCg3XfffVpaWppGykEev337tkY/YI0Ektbe3q5duHBB83g82vbt281Bdc0kkJxaHnK07/V6NyphA6EObQUBP+rkyZMv6kNP+jzTxgLQrl69+iUJfQidsYFG3KiD+qpuqs2oOVNdB4IssaioaDH1wxUc27t37y8DnJOsn7N8+fIMPBOOkWL5O+2LMI7CSWFXw8DT61uUmDCU8Ua9L7Bdv379/AB1i/R+wHb16tWLA7SrmwWhn/Ptt9+W6u0KYIH0ON9p2/X20Hvfaqo/lgYw6/V7lJWVTeKfNsP0P0VGgY9sq0WLFmkPP/ywLFAaNOqXZdq0abIOCQmNrBFZvv/+e78f4eOPP9Y+/PBDswIpClHgFRkERKZSHLaCUQmeaCsFQiPUndiWlJTk2o24jfWUcJsUTOgZjm02PGu0w3PkPaF8dOVqEqKpffly9X7S26iedbBN3RYoGjwH6pKSfMZYN5ACwPV1JXL48OFlYSqQVKftUe1ItHNfHj9+/A27djIM05NwYyB+F866detk4JysCxksJ8tCuq/IApExj8TErt8r/j1y5EhZBg0aJEiJiCtXroh58+bJ+nBlWV3fgXCAQM3t7Oxsf+6553bRZ6R7XbKp/ha8TrGxsZkk6OZbuZBOnDgh3SSzZs1aZjN6fwp/9uzZY3SdhCJ02qxcRYGg/pGJBRERETGiFzGiEMgy9kVKSgqsijiLvsd7iv3iiy/MbqRIJzeh70JqdXX1Fnx+6KGHCumdJP6Xfgf/wp/o6Og71b8Mc9cqkGT9R5aamirKy8ul8P/mm2/gL5dB88bGRggfmW2F46ChoUHW+e677wSNWP11z58/LwPsqP/aa68ZBatTN5YU/GThVFZUVCA+cD6AIMZxOQM+PT09y2yFwEe+ZMmSCnweM2ZMlo0lk4t6L7/8MmIerWH0n1RABw4cqAhRScrns3P19AdkGdYjnhQZGZlQWFg4064tJPgr6RnD6Qsxe/bsEtpU4B5ZWVnr72T7DIzDHxr8oH8HsVhgmP5VIGLBggVi8ODB/tTcuLg4kZGRIQvmf9xzzz3S+oDFAR544AF/fWRgIcCOAssEdfX627Zt63YfB0zBn9OnT9cogd4ZpD6WUhEJCQk/p81Q44EbN24gntEBJYPRPilAt9WI+9y5cxWqnrQMVq9eHXTkrNxQCPInI7geogJCYoFQAeOOO/Xl2LJlS9PAgQMh4EV2dvYyk8sNSt5NA4F61KP3Jyf3IGkhjFutUd+R33u93jl38gegkgCkBZufn4/3eovFAsP0rwsLAlhkZmZKxTBt2jQ536OtrU1cvnxZbqEskMoLxaJDo3qpMIzcvn1b1l2xYkWP+g6RKbfIuKJNu4P6Pvy59957E3SBaErvhQDZjw+TJ0+eb3JpGN1XfuFP7U+wcmPRdasNPnzMl3GdOnXq7ZSUlALRldXUI8uLRvOZysfv0tNPIaiRnZWWloYMom7uObjjqM6XVnmsvfhe+Ptj2LBhUoEgY8lkkeXij3JfXadBgVRs8fHxln0RCOWie0v15VazZWhHqG0fPnx44uHDh2ca+heK2QvlUVBQ8KyyYFtZLDCMM8I2148ePSpTdkkQy1nmiIEogeO3LPA7vnnzptwP95Ve9/r163I/lBDqjh49WtaBItHrh0moo/PBNtYO3FxFyo0FBdKqj7gN7itznCXSfH8oC/0zUnLJGsucOHHiM2TpTIqKispG7KeHfyw3d6t5H65jUB5NZrebXSqrsE+pdaxAMAmT2l4XGRmZUVhYOP35558/a3Zf2fRFqOSj+fQdSa2vr1+fmpr6h2AnhNp2UoKLUMzXWLt27bNkRaFd9Q4sWIZheqtAkpKSpNVBwlCQcJEKQ59ACIWA+R5QDpiNjvgG6pvrDhkypNs1s7KyZP0QkSNGEs5O01WlRXHt2rXmACNiKAy4sdxwY2VnZ2N0LN1ZBvfV9WA3UkLff5/ly5fHb9269Q3qo/lXrlyBoviNWWB5PJ5n9c+PPPKIa/z48U9A6Zw8efKfdD2P+R5wu9H+vwr7xIG+oBiWHtxYpEAOUt/E49+6+6ovRu2qzzE3ppTa/EJJScn7OTk5AVclCLXtsOI++uijD3RXG1k7T0Bhbdq06Q1qx6Q76R5kmLtVgUgXEOIVUAAYRcOFNXDgQGlxtLa2SksCwXFkZGEioQ7qT5gwwfbCNPI01vc5fB5k0LgffPBBpHM6CcDKDCOyhL40C4zLly8bJwPCjeVWbiyPfl5BQcEug8D06cIowP38FsPu3bubSDD+ij42kKWW8+STT/7p3Xff/dxYeeXKlTXix0mJu7766quylJSUv1F5XVlGVsL6lgh9smBAoBxMFtlmgxsLW3H8+PFdSpF26H0BN1EvlMg++g5VkOJ2kfLcQLt+7eA0x21va2trov4tNyicQrrfP0iJZNTW1uZNnTp1E4sEhul/BdLq8/li4cJCvKOjo0MKflgXsCygVHAMqbokXLt8S1QnWF1kban6rSEoEFgEG1Sqab6D0bC0JD755JMagxUhBaKaNX7D6MaKi4vLVFaL2zDi1jO9/o0/ofj91UgbI2vXo48+OpMUyCkLt4k/lkOKcQfV/yP1VzIpHzeNyj39+YXQl/Wg99Gu94/RjfXSSy/9gnYtkT6nrqDzBaMyVbGl3sylgBVSS1aqe+/evXgW9FVfrtbcIbrHyv6C90zfuxzabutnS45h2IUF4TpixIhcfIDlAYsDwXS4rXQFAVcWLBIatSJ7yB9UxxwQ7DOi16XRtn7M8X82RcKtgs71QcAeO3bsqRkzZvw5gHDEMydDEag4xlWLap1GNxZd1+31enEe5jtsM4y4zYTi95duNLLQIMiiRfDgP/ojLy0tDam07wtnyQJ9QafZjbVw4cJZUKYXL16sINptFHbYCkQpKwj1DXPnzn2dlPqNqKio/myjHCggIK+sK1YgDOOQcLOw8pF2O27cODlZEPNBkLoLFxXSdBH7wD6siQWF4tdWg6z1Fc6Ljo421s8P8XlkGmhmZuZ6q2VKlPLAKHazciUVKEUQLI4hs7HmzJmzFlubgHGoI3z5vzUi80cpMSdBW5l6jPW0RBhLk/ShoPX3BfVzpXCWNh2OEtkIywNCnb5n6f3ZKDU3qE69XxeLBIbpfwvEt2fPHs/IkSNz4X7SZ5arH6R0T0Ep4JjOp59+KrOwUBdKAplYcGEZ68KF9eqrr3pCcF/p94Tv/K2IiIi8iRMnlqkR7D6khyrFAaH9Akb+NGrOV3GGRsMlhuMPWUD1VqNTzAnBiNsuYOzE769cQ3D9yNVta2tr31bC97qDJlZIs6VrlNxt7goJ2Jh9+/ZNX7JkidUztOqz2EO1jkzxIL8bi/pCKj+yDj6w6gt6l301mxyDAq+afW9JH7Yd/Zsxffp0XUG3s2hgmP4ldsWKFdqCBQu0xYsXawsXLpSFBIs2a9YsbfLkydqYMWM0EnpyfSsSOrbrbpNC0UgQoF6L6MVSEqQAfquvrWQG6yapdZp6rJWlr4OljpuXTS81LNKYYlYKhjWZkg37bcHzqTWX8Bzx5nOExVpY6jiWdtf279//ovHegSClfkg4nFNhuI9x3aixpmNymffGxkYojwyLc3usDdabtaz0dcPsznfadgdrYbn1xSOtjjMM07cWiBzhvffee1NfeeWVWlgPyL7C2lawLhDvQLYVJhpi2ZLdu3fLWEmAkaSenTVX9CIlFAFn2hwoLCycn5SUlIzMrKqqqhoS2M3KesDIstlihLmGBHN6cXFxo4VLZs3BgwdLNm3a1GzxbHUNDQ3Z1D4oHaPff251dfUitbYSrK32EydO1CPmodxW8NMhEG9cIn2ux+MJtDDgUnrG2eXl5W1Kycl7V1ZW2q4arGIsPxPdl5oPhufIkSOf79y5s8OiLzw1NTW+d955p9PmPeltGBykXcZ+C0Q+Pcvh06dPj7I6P4S2G9tkacGeOXNGvx6s0SYWDQzjwPvTB9dwDxkypBRzPHSgQDDrHHENBEDr6urkGlhnz3bNQcM6WJh4iP/2FnXhuiJFtFSEEDx3QLQSZHqQ+pYInOePehHKpWQWnLhOpM2xCHWu2R0F5THEoKRvi64Mr0BuK91dY+dC0Z9Db0uEAwvDqZss0H2s2mvXn1ZtsNpn12/C5n525ztte6A2Oe1/hmH6WIEI5c4oysnJyUBMA8uZIBMLAXXENw4dOiT3RUREyJnqptEf/NRI3azj18EwDHP3KRCdXCobli1bhlRZucw7gurFxcXS4oC1YVAcPtGVbeXh18AwDMMKRMetrJIsi2OVytrYx93PMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAzDMAwjxH8EGABIqoQ6dJhDnAAAAABJRU5ErkJggg==');
            }

            .hashrate-tooltip{
                color: #333;
            }

            .sumokoin-org-link{
                text-align:left;
                margin-left:34px;
                margin-top: 32px;
                margin-bottom: 0;
                font-size:90%;
                color: #010100;
                /*font-weight: bold;
                font-family: "Lucida Console", "Courier New", Monaco, Courier, monospace;*/
            }

            .sumokoin-org-link a{
                color: #010100;
                cursor: pointer;
            }

            .sumokoin-org-link a:hover{
                color: #010100;

            }
        </style>
    </head>
    <body>
            <table width="100%" height="100%" border="0" cellpadding="0" cellspacing="0" id="pools_table">
                <thead>
                    <tr style="height:50px;background: -webkit-linear-gradient(top, #bcc3ca 0%,#919294 30%,#eef4fb 100%);">
                        <th colspan="5" style="" class="banner">
                            <p class="sumokoin-org-link">v0.1 (Beta 1.3) by <a href="#" onclick="open_link('https://www.ombre.io')">www.ombre.io</a></p>
                        </th>
                        <th colspan="5" class="pool-btns">
                            <a href="#" onclick="addPool()"><i class="fa fa-plus"></i> Add Pool</a> | <a href="#" onclick="showAllPools()"><i class="fa fa-eye"></i> Show All</a> | <a href="#" onclick="quitApp()"><i class="fa fa-sign-out"></i> Exit</a>
                        </th>
                    </tr>
                    <tr style="border-top: 1px solid #aaa;">
                        <th width="15%" style="text-align: left; padding-left: 1em;line-height:1.7em;">Pool Name</th>
                        <th width="7%" style="text-align: left; padding-left: 1em;">Start/Stop</th>
                        <th width="7%">&nbsp;</th>
                        <th width="7%">Threads</th>
                        <th width="7%">Priority</th>
                        <th width="20%">Hash Rate</th>
                        <th width="8%">Shares<br/><span style="font-size:80%;">(Good/Total)</span></th>
                        <th width="8%">Difficulty</th>
                        <th width="12%">Action</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- template insert here-->
                </tbody>
                <tfoot>
                </tfoot>
            </table>
        </div>
        <script id="template" type="x-tmpl-mustache">
            <tr id="{{ pool_id }}" style="display:{{ pool_hidden }};">
                <td style="text-align: left; padding-left: 1em;"><span class="pool-name">{{ pool_name }}</span></td>
                <td width="7%" class="btn-start-col"> <a href="#" class="btn-start" onclick="startStopMining('{{ pool_id }}')" title="Start/Stop mining"><i class="fa fa-play"></i>&nbsp;&nbsp;<span class="btn-start-text">Start</span></a></td>
                <td width="16%" class="mining-status-col"><span class="mining-status">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></td><input type="hidden" class="is-mining" value="0">
                <td>
                    <select style="width:40px; font-size:100%" class="num_cpus" onchange="changeCPUCores(this, '{{ pool_id }}')"
                            title="Select number of mining threads. TIP: By default, number of mining threads is equal to number of CPU cores, yet in many cases, increasing or decreasing mining threads will result in better performance.">
                        {{{ option_html }}}
                    </select>
                </td>
                <td>
                    <select style="width:70px; font-size:100%" class="cpu_priority" onchange="changePriority(this, '{{ pool_id }}')"
                            title="Select CPU priority level.">
                        {{{ option_html2 }}}
                    </select>
                </td>
                <td style="font-size:90%;">
                    <span class="hashrate">0.00 H/s</span>
                    <div class="rate-chart"></div>
                    avg: <span class="hashrate-avg">0.00 H/s</span> - max: <span class="hashrate-max">0.00 H/s</span>
                </td>
                <td style="text-align:center;font-size:90%;">
                    <span class="shares">0/0</span>
                    <div class="shares-chart"></div>
                    <small><span class="shares-pct">0.00%</span></small>
                </td>
                <td><span class="difficulty">0</span></td>
                <td style="text-align: left; padding-left: 1.5em;"><a class="view-log" href="#" onclick="viewLog('{{ pool_id }}')" title="View Log"><i class="fa fa-file-code-o"></i></a>
                    &nbsp;&nbsp;&nbsp;<a class="hide-pool" href="#" onclick="hidePool('{{ pool_id }}')" title="Hide"><i class="fa fa-eye-slash"></i></a>
                    &nbsp;&nbsp;&nbsp;<a class="edit-pool" href="#" onclick="editPool('{{ pool_id }}')" title="Edit"><i class="fa fa-edit"></i></a>
                    &nbsp;&nbsp;&nbsp;<a class="remove-pool" href="#" onclick="removePool('{{ pool_id }}')" style="display: {{pool_removable}}" title="Remove"><i class="fa fa-trash-o"></i></a>
                </td>
            </tr>
        </script>
    </body>
</html>
"""
